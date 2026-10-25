/*
 * Intel ACPI Component Architecture
 * AML/ASL+ Disassembler version 20190509 (64-bit version)
 * Copyright (c) 2000 - 2019 Intel Corporation
 * 
 * Disassembly of FPDT0000.bin, Wed Jun 16 09:46:15 2021
 *
 * ACPI Data Table [FPDT]
 *
 * Format: [HexOffset DecimalOffset ByteLength]  FieldName : FieldValue
 */

[000h 0000   4]                    Signature : "FPDT"    [Firmware Performance Data Table]
[004h 0004   4]                 Table Length : 00000034
[008h 0008   1]                     Revision : 01
[009h 0009   1]                     Checksum : EA
[00Ah 0010   6]                       Oem ID : "NVIDIA"
[010h 0016   8]                 Oem Table ID : "AP30EDK2"
[018h 0024   4]                 Oem Revision : 00000003
[01Ch 0028   4]              Asl Compiler ID : "MSFT"
[020h 0032   4]        Asl Compiler Revision : 04000000


[024h 0036   2]                Subtable Type : 0000
[026h 0038   1]                       Length : 10
[027h 0039   1]                     Revision : 01
[028h 0040   4]                     Reserved : 00000000
[02Ch 0044   8]     FPDT Boot Record Address : 00000000FD908F90

Raw Table Data: Length 52 (0x34)

    0000: 46 50 44 54 34 00 00 00 01 EA 4E 56 49 44 49 41  // FPDT4.....NVIDIA
    0010: 41 50 33 30 45 44 4B 32 03 00 00 00 4D 53 46 54  // AP30EDK2....MSFT
    0020: 00 00 00 04 00 00 10 01 00 00 00 00 90 8F 90 FD  // ................
    0030: 00 00 00 00                                      // ....
