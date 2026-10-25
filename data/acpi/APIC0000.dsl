/*
 * Intel ACPI Component Architecture
 * AML/ASL+ Disassembler version 20190509 (64-bit version)
 * Copyright (c) 2000 - 2019 Intel Corporation
 * 
 * Disassembly of APIC0000.bin, Wed Jun 16 09:46:15 2021
 *
 * ACPI Data Table [APIC]
 *
 * Format: [HexOffset DecimalOffset ByteLength]  FieldName : FieldValue
 */

[000h 0000   4]                    Signature : "APIC"    [Multiple APIC Description Table (MADT)]
[004h 0004   4]                 Table Length : 000000E4
[008h 0008   1]                     Revision : 03
[009h 0009   1]                     Checksum : 67
[00Ah 0010   6]                       Oem ID : "NVIDIA"
[010h 0016   8]                 Oem Table ID : "AP30EDK2"
[018h 0024   4]                 Oem Revision : 02000820
[01Ch 0028   4]              Asl Compiler ID : "AP30"
[020h 0032   4]        Asl Compiler Revision : 00000097

[024h 0036   4]           Local Apic Address : 50040100
[028h 0040   4]        Flags (decoded below) : 00000000
                         PC-AT Compatibility : 0

[02Ch 0044   1]                Subtable Type : 0B [Generic Interrupt Controller]
[02Dh 0045   1]                       Length : 28
[02Eh 0046   2]                     Reserved : 0000
[030h 0048   4]         CPU Interface Number : 00000000
[034h 0052   4]                Processor UID : 00000000
[038h 0056   4]        Flags (decoded below) : 00000001
                           Processor Enabled : 1
          Performance Interrupt Trigger Mode : 0
          Virtual GIC Interrupt Trigger Mode : 0
[03Ch 0060   4]     Parking Protocol Version : 00000001
[040h 0064   4]        Performance Interrupt : 000000B0
[044h 0068   8]               Parked Address : 0000000082001000
[04Ch 0076   8]                 Base Address : 0000000000000000
/**** ACPI subtable terminates early - may be older version (dump table) */

[054h 0084   1]                Subtable Type : 0B [Generic Interrupt Controller]
[055h 0085   1]                       Length : 28
[056h 0086   2]                     Reserved : 0000
[058h 0088   4]         CPU Interface Number : 00000001
[05Ch 0092   4]                Processor UID : 00000001
[060h 0096   4]        Flags (decoded below) : 00000001
                           Processor Enabled : 1
          Performance Interrupt Trigger Mode : 0
          Virtual GIC Interrupt Trigger Mode : 0
[064h 0100   4]     Parking Protocol Version : 00000001
[068h 0104   4]        Performance Interrupt : 000000B1
[06Ch 0108   8]               Parked Address : 0000000082002000
[074h 0116   8]                 Base Address : 0000000000000000
/**** ACPI subtable terminates early - may be older version (dump table) */

[07Ch 0124   1]                Subtable Type : 0B [Generic Interrupt Controller]
[07Dh 0125   1]                       Length : 28
[07Eh 0126   2]                     Reserved : 0000
[080h 0128   4]         CPU Interface Number : 00000002
[084h 0132   4]                Processor UID : 00000002
[088h 0136   4]        Flags (decoded below) : 00000001
                           Processor Enabled : 1
          Performance Interrupt Trigger Mode : 0
          Virtual GIC Interrupt Trigger Mode : 0
[08Ch 0140   4]     Parking Protocol Version : 00000001
[090h 0144   4]        Performance Interrupt : 000000B2
[094h 0148   8]               Parked Address : 0000000082003000
[09Ch 0156   8]                 Base Address : 0000000000000000
/**** ACPI subtable terminates early - may be older version (dump table) */

[0A4h 0164   1]                Subtable Type : 0B [Generic Interrupt Controller]
[0A5h 0165   1]                       Length : 28
[0A6h 0166   2]                     Reserved : 0000
[0A8h 0168   4]         CPU Interface Number : 00000003
[0ACh 0172   4]                Processor UID : 00000003
[0B0h 0176   4]        Flags (decoded below) : 00000001
                           Processor Enabled : 1
          Performance Interrupt Trigger Mode : 0
          Virtual GIC Interrupt Trigger Mode : 0
[0B4h 0180   4]     Parking Protocol Version : 00000001
[0B8h 0184   4]        Performance Interrupt : 000000B3
[0BCh 0188   8]               Parked Address : 0000000082004000
[0C4h 0196   8]                 Base Address : 0000000000000000
/**** ACPI subtable terminates early - may be older version (dump table) */

[0CCh 0204   1]                Subtable Type : 0C [Generic Interrupt Distributor]
[0CDh 0205   1]                       Length : 18
[0CEh 0206   2]                     Reserved : 0000
[0D0h 0208   4]        Local GIC Hardware ID : 00000000
[0D4h 0212   8]                 Base Address : 0000000050041000
[0DCh 0220   4]               Interrupt Base : 00000000
[0E0h 0224   1]                      Version : 00
[0E1h 0225   3]                     Reserved : 000000

Raw Table Data: Length 228 (0xE4)

    0000: 41 50 49 43 E4 00 00 00 03 67 4E 56 49 44 49 41  // APIC.....gNVIDIA
    0010: 41 50 33 30 45 44 4B 32 20 08 00 02 41 50 33 30  // AP30EDK2 ...AP30
    0020: 97 00 00 00 00 01 04 50 00 00 00 00 0B 28 00 00  // .......P.....(..
    0030: 00 00 00 00 00 00 00 00 01 00 00 00 01 00 00 00  // ................
    0040: B0 00 00 00 00 10 00 82 00 00 00 00 00 00 00 00  // ................
    0050: 00 00 00 00 0B 28 00 00 01 00 00 00 01 00 00 00  // .....(..........
    0060: 01 00 00 00 01 00 00 00 B1 00 00 00 00 20 00 82  // ............. ..
    0070: 00 00 00 00 00 00 00 00 00 00 00 00 0B 28 00 00  // .............(..
    0080: 02 00 00 00 02 00 00 00 01 00 00 00 01 00 00 00  // ................
    0090: B2 00 00 00 00 30 00 82 00 00 00 00 00 00 00 00  // .....0..........
    00A0: 00 00 00 00 0B 28 00 00 03 00 00 00 03 00 00 00  // .....(..........
    00B0: 01 00 00 00 01 00 00 00 B3 00 00 00 00 40 00 82  // .............@..
    00C0: 00 00 00 00 00 00 00 00 00 00 00 00 0C 18 00 00  // ................
    00D0: 00 00 00 00 00 10 04 50 00 00 00 00 00 00 00 00  // .......P........
    00E0: 00 00 00 00                                      // ....
