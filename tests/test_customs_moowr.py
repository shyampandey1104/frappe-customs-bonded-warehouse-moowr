import unittest
from customs_moowr.engine import IntoBondBillOfEntry, MOOWRCustomsBondedEngine

class TestMOOWRCustomsBondedEngine(unittest.TestCase):
    def setUp(self):
        self.engine = MOOWRCustomsBondedEngine(
            customs_bond_number="BOND/JNPT/2026/088", bond_capacity_inr=10000000.0
        )

    def test_into_bond_processing(self):
        boe = IntoBondBillOfEntry(
            boe_number="BOE/JNPT/IN/778912", port_code="INNSA1", boe_date="2026-03-10",
            warehouse_license_no="WH/LIC/MUM/004", cif_value_inr=1000000.0,
            assessable_value_inr=1000000.0, basic_customs_duty_rate=7.5, igst_rate=18.0
        )
        res = self.engine.process_into_bond_entry(boe, item_code="RAW-SILICON-INGOT", qty=500.0)
        self.assertGreater(res["total_deferred_duty"], 0)
        self.assertEqual(self.engine.utilized_bond_inr, res["total_deferred_duty"])

    def test_ex_bond_export_waiver(self):
        boe = IntoBondBillOfEntry(
            boe_number="BOE/JNPT/IN/778913", port_code="INNSA1", boe_date="2026-03-10",
            warehouse_license_no="WH/LIC/MUM/004", cif_value_inr=1000000.0,
            assessable_value_inr=1000000.0, basic_customs_duty_rate=10.0, igst_rate=18.0
        )
        self.engine.process_into_bond_entry(boe, item_code="SMD-CAPACITORS", qty=1000.0)
        
        # Export 800 units
        res = self.engine.discharge_ex_bond_export(boe.boe_number, 800.0, "SB/JNPT/EXP/4412")
        self.assertEqual(res["interest_payable_inr"], 0.0)
        self.assertEqual(res["remaining_balance_in_bond"], 200.0)
        self.assertEqual(res["status"], "DISCHARGED_DUTY_WAIVED")

    def test_ex_bond_domestic_clearance(self):
        boe = IntoBondBillOfEntry(
            boe_number="BOE/JNPT/IN/778914", port_code="INNSA1", boe_date="2026-03-10",
            warehouse_license_no="WH/LIC/MUM/004", cif_value_inr=500000.0,
            assessable_value_inr=500000.0, basic_customs_duty_rate=10.0, igst_rate=18.0
        )
        self.engine.process_into_bond_entry(boe, item_code="SMD-RESISTORS", qty=500.0)
        res = self.engine.discharge_ex_bond_domestic(boe.boe_number, 200.0, "EX-BOE-JNPT-091")
        self.assertEqual(res["interest_payable_inr"], 0.0)
        self.assertEqual(res["remaining_balance_in_bond"], 300.0)

if __name__ == "__main__":
    unittest.main()
