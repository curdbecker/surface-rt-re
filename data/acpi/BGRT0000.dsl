/*
 * Intel ACPI Component Architecture
 * AML/ASL+ Disassembler version 20190509 (64-bit version)
 * Copyright (c) 2000 - 2019 Intel Corporation
 * 
 * Disassembly of BGRT0000.bin, Wed Jun 16 09:46:15 2021
 *
 * ACPI Data Table [BGRT]
 *
 * Format: [HexOffset DecimalOffset ByteLength]  FieldName : FieldValue
 */

[000h 0000   4]                    Signature : "BGRT"    [Boot Graphics Resource Table]
[004h 0004   4]                 Table Length : 00000038
[008h 0008   1]                     Revision : 01
[009h 0009   1]                     Checksum : A3
[00Ah 0010   6]                       Oem ID : "NVIDIA"
[010h 0016   8]                 Oem Table ID : "AP30EDK2"
[018h 0024   4]                 Oem Revision : 00000003
[01Ch 0028   4]              Asl Compiler ID : "MSFT"
[020h 0032   4]        Asl Compiler Revision : 04000000

[024h 0036   2]                      Version : 0001
[026h 0038   1]       Status (decoded below) : 01
                                   Displayed : 1
                          Orientation Offset : 0
[027h 0039   1]                   Image Type : 00
[028h 0040   8]                Image Address : 00000000FD548010
[030h 0048   4]                Image OffsetX : 0000021B
[034h 0052   4]                Image OffsetY : 000000FF

Raw Table Data: Length 56 (0x38)

    0000: 42 47 52 54 38 00 00 00 01 A3 4E 56 49 44 49 41  // BGRT8.....NVIDIA
    0010: 41 50 33 30 45 44 4B 32 03 00 00 00 4D 53 46 54  // AP30EDK2....MSFT
    0020: 00 00 00 04 01 00 01 00 10 80 54 FD 00 00 00 00  // ..........T.....
    0030: 1B 02 00 00 FF 00 00 00                          // ........
