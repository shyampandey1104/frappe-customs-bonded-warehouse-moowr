"""MOOWR (Manufacturing and Other Operations in Warehouse Regulations) Scheme Engine."""
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import List, Dict, Any, Optional

@dataclass
class IntoBondBillOfEntry:
    boe_number: str
    port_code: str
    boe_date: str
    warehouse_license_no: str
    cif_value_inr: float
    assessable_value_inr: float
    basic_customs_duty_rate: float  # e.g., 7.5%
    igst_rate: float                # e.g., 18.0%
    deferred_bcd: float = 0.0
    deferred_igst: float = 0.0
    total_deferred_duty: float = 0.0

@dataclass
class BondRegisterEntry:
    transaction_id: str
    boe_number: str
    raw_material_code: str
    quantity_received: float
    quantity_consumed_for_export: float = 0.0
    quantity_consumed_for_domestic: float = 0.0
    balance_in_bond: float = 0.0

class MOOWRCustomsBondedEngine:
    def __init__(self, customs_bond_number: str, bond_capacity_inr: float):
        self.customs_bond_number = customs_bond_number
        self.bond_capacity_inr = bond_capacity_inr
        self.utilized_bond_inr: float = 0.0
        self.into_bond_records: Dict[str, IntoBondBillOfEntry] = {}
        self.bond_register: Dict[str, BondRegisterEntry] = {}

    def process_into_bond_entry(self, boe: IntoBondBillOfEntry, item_code: str, qty: float) -> Dict[str, Any]:
        bcd = round(boe.assessable_value_inr * (boe.basic_customs_duty_rate / 100.0), 2)
        # SWS (Social Welfare Surcharge) @ 10% of BCD
        sws = round(bcd * 0.10, 2)
        taxable_for_igst = boe.assessable_value_inr + bcd + sws
        igst = round(taxable_for_igst * (boe.igst_rate / 100.0), 2)
        total_duty = round(bcd + sws + igst, 2)

        if (self.utilized_bond_inr + total_duty) > self.bond_capacity_inr:
            raise ValueError(f"Duty liability ₹{total_duty} exceeds available Customs Bond balance.")

        boe.deferred_bcd = bcd + sws
        boe.deferred_igst = igst
        boe.total_deferred_duty = total_duty
        self.utilized_bond_inr += total_duty
        self.into_bond_records[boe.boe_number] = boe

        reg = BondRegisterEntry(
            transaction_id=f"BOND-IN-{boe.boe_number}",
            boe_number=boe.boe_number,
            raw_material_code=item_code,
            quantity_received=qty,
            balance_in_bond=qty
        )
        self.bond_register[boe.boe_number] = reg

        return {
            "boe_number": boe.boe_number,
            "total_deferred_duty": total_duty,
            "remaining_bond_capacity": round(self.bond_capacity_inr - self.utilized_bond_inr, 2)
        }

    def discharge_ex_bond_export(self, boe_number: str, export_qty: float, shipping_bill_no: str) -> Dict[str, Any]:
        if boe_number not in self.bond_register:
            raise ValueError(f"BoE {boe_number} not in bond register.")
        reg = self.bond_register[boe_number]
        if export_qty > reg.balance_in_bond:
            raise ValueError(f"Export qty {export_qty} exceeds bond balance {reg.balance_in_bond}.")

        boe = self.into_bond_records[boe_number]
        duty_per_unit = boe.total_deferred_duty / reg.quantity_received
        waived_duty = round(duty_per_unit * export_qty, 2)

        reg.balance_in_bond -= export_qty
        reg.quantity_consumed_for_export += export_qty
        self.utilized_bond_inr = max(0.0, round(self.utilized_bond_inr - waived_duty, 2))

        return {
            "boe_number": boe_number,
            "shipping_bill_no": shipping_bill_no,
            "waived_duty_inr": waived_duty,
            "interest_payable_inr": 0.0,  # Under MOOWR, export duty is 100% waived with NO interest
            "remaining_balance_in_bond": reg.balance_in_bond,
            "status": "DISCHARGED_DUTY_WAIVED"
        }

    def discharge_ex_bond_domestic(self, boe_number: str, domestic_qty: float, ex_bond_boe_no: str) -> Dict[str, Any]:
        if boe_number not in self.bond_register:
            raise ValueError(f"BoE {boe_number} not in bond register.")
        reg = self.bond_register[boe_number]
        if domestic_qty > reg.balance_in_bond:
            raise ValueError(f"Domestic qty {domestic_qty} exceeds bond balance {reg.balance_in_bond}.")

        boe = self.into_bond_records[boe_number]
        duty_per_unit = boe.total_deferred_duty / reg.quantity_received
        payable_duty = round(duty_per_unit * domestic_qty, 2)

        reg.balance_in_bond -= domestic_qty
        reg.quantity_consumed_for_domestic += domestic_qty
        self.utilized_bond_inr = max(0.0, round(self.utilized_bond_inr - payable_duty, 2))

        return {
            "boe_number": boe_number,
            "ex_bond_boe_no": ex_bond_boe_no,
            "customs_duty_payable": payable_duty,
            "interest_payable_inr": 0.0,  # Sec 65 MOOWR waives Sec 61 interest on deferred duty!
            "remaining_balance_in_bond": reg.balance_in_bond,
            "status": "DUTY_PAYABLE_NO_INTEREST"
        }
