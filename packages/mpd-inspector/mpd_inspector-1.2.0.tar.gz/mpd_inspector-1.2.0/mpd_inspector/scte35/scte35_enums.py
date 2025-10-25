import enum


class SpliceCommandType(enum.Enum):
    SPLICE_INSERT = 5
    TIME_SIGNAL = 6
    SPLICE_NULL = 7
    BANDWIDTH_RESERVATION = 8
    PRIVATE = 9
    SPLICE_SCHEDULE = 10

    def __str__(self):
        return f"{self.name.lower()} (0x{self.value:02x})"


class SegmentationType:
    @staticmethod
    def get_name(value: int) -> str:
        return table22[value]

    @staticmethod
    def from_name(name: str) -> int:
        # reverse lookup
        for key, value in table22.items():
            if value == name or name.replace(" ", "") == value:
                return key
        raise ValueError(f"No value found for {name}")

    @staticmethod
    def to_hexstring(int_value: int) -> str:
        return f"0x{int_value:02x}"


table22 = {
    0x00: "Not Indicated",
    0x01: "Content Identification",
    0x02: "Call Ad Server",
    0x10: "Program Start",
    0x11: "Program End",
    0x12: "Program Early Termination",
    0x13: "Program Breakaway",
    0x14: "Program Resumption",
    0x15: "Program Runover Planned",
    0x16: "Program RunoverUnplanned",
    0x17: "Program Overlap Start",
    0x18: "Program Blackout Override",
    0x19: "Program Start ??? In Progress",
    0x20: "Chapter Start",
    0x21: "Chapter End",
    0x22: "Break Start",
    0x23: "Break End",
    0x30: "Provider Advertisement Start",
    0x31: "Provider Advertisement End",
    0x32: "Distributor Advertisement Start",
    0x33: "Distributor Advertisement End",
    0x34: "Provider Placement Opportunity Start",
    0x35: "Provider Placement Opportunity End",
    0x36: "Distributor Placement Opportunity Start",
    0x37: "Distributor Placement Opportunity End",
    0x38: "Provider Overlay Placement Opportunity Start",
    0x39: "Provider Overlay Placement Opportunity End",
    0x3A: "Distributor Overlay Placement Opportunity Start",
    0x3B: "Distributor Overlay Placement Opportunity End",
    0x3C: "Provider Promo Start",
    0x3D: "Provider Promo End",
    0x3E: "Distributor Promo Start",
    0x3F: "Distributor Promo End",
    0x40: "Unscheduled Event Start",
    0x41: "Unscheduled Event End",
    0x42: "Alternate Content Opportunity Start",
    0x43: "Alternate Content Opportunity End",
    0x44: "Provider Ad Block Start",
    0x45: "Provider Ad Block End",
    0x46: "Distributor Ad Block Start",
    0x47: "Distributor Ad Block End",
    0x50: "Network Start",
    0x51: "Network End",
}
