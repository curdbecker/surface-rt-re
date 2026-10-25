/*
 * Intel ACPI Component Architecture
 * AML/ASL+ Disassembler version 20190509 (64-bit version)
 * Copyright (c) 2000 - 2019 Intel Corporation
 * 
 * Disassembly of DBG20000.bin, Wed Jun 16 09:46:15 2021
 *
 * ACPI Data Table [DBG2]
 *
 * Format: [HexOffset DecimalOffset ByteLength]  FieldName : FieldValue
 */

[000h 0000   4]                    Signature : "DBG2"    [Debug Port table type 2]
[004h 0004   4]                 Table Length : 000000A8
[008h 0008   1]                     Revision : 00
[009h 0009   1]                     Checksum : 16
[00Ah 0010   6]                       Oem ID : "NVIDIA"
[010h 0016   8]                 Oem Table ID : "AP30EDK2"
[018h 0024   4]                 Oem Revision : 02000820
[01Ch 0028   4]              Asl Compiler ID : "AP30"
[020h 0032   4]        Asl Compiler Revision : 00000097

[024h 0036   4]                  Info Offset : 0000002C
[028h 0040   4]                   Info Count : 00000002

[02Ch 0044   1]                     Revision : 00
[02Dh 0045   2]                       Length : 0036
[02Fh 0047   1]               Register Count : 01
[030h 0048   2]              Namepath Length : 0010
[032h 0050   2]              Namepath Offset : 0026
[034h 0052   2]              OEM Data Length : 0000 [Optional field not present]
[036h 0054   2]              OEM Data Offset : 0000 [Optional field not present]
[038h 0056   2]                    Port Type : 8000
[03Ah 0058   2]                 Port Subtype : 0005
[03Ch 0060   2]                     Reserved : 0000
[03Eh 0062   2]          Base Address Offset : 0016
[040h 0064   2]          Address Size Offset : 0022

[042h 0066  12]        Base Address Register : [Generic Address Structure]
[042h 0066   1]                     Space ID : 00 [SystemMemory]
[043h 0067   1]                    Bit Width : 00
[044h 0068   1]                   Bit Offset : 00
[045h 0069   1]         Encoded Access Width : 03 [DWord Access:32]
[046h 0070   8]                      Address : 0000000070006000

[04Eh 0078   4]                 Address Size : 00000040

[052h 0082  10]                     Namepath : "\_SB.UAR1"

[062h 0098   1]                     Revision : 00
[063h 0099   2]                       Length : 0046
[065h 0101   1]               Register Count : 02
[066h 0102   2]              Namepath Length : 0010
[068h 0104   2]              Namepath Offset : 0036
[06Ah 0106   2]              OEM Data Length : 0000 [Optional field not present]
[06Ch 0108   2]              OEM Data Offset : 0000 [Optional field not present]
[06Eh 0110   2]                    Port Type : 8002
[070h 0112   2]                 Port Subtype : 0006
[072h 0114   2]                     Reserved : 0000
[074h 0116   2]          Base Address Offset : 0016
[076h 0118   2]          Address Size Offset : 002E

[078h 0120  12]        Base Address Register : [Generic Address Structure]
[078h 0120   1]                     Space ID : 00 [SystemMemory]
[079h 0121   1]                    Bit Width : 00
[07Ah 0122   1]                   Bit Offset : 00
[07Bh 0123   1]         Encoded Access Width : 03 [DWord Access:32]
[07Ch 0124   8]                      Address : 000000007D000000


[084h 0132  12]        Base Address Register : [Generic Address Structure]
[084h 0132   1]                     Space ID : 00 [SystemMemory]
[085h 0133   1]                    Bit Width : 00
[086h 0134   1]                   Bit Offset : 00
[087h 0135   1]         Encoded Access Width : 03 [DWord Access:32]
[088h 0136   8]                      Address : 00000000FD5B8000

[090h 0144   4]                 Address Size : 00004000
[094h 0148   4]                 Address Size : 00004000

[098h 0152  10]                     Namepath : "\_SB.WDBG"

Raw Table Data: Length 168 (0xA8)

    0000: 44 42 47 32 A8 00 00 00 00 16 4E 56 49 44 49 41  // DBG2......NVIDIA
    0010: 41 50 33 30 45 44 4B 32 20 08 00 02 41 50 33 30  // AP30EDK2 ...AP30
    0020: 97 00 00 00 2C 00 00 00 02 00 00 00 00 36 00 01  // ....,........6..
    0030: 10 00 26 00 00 00 00 00 00 80 05 00 00 00 16 00  // ..&.............
    0040: 22 00 00 00 00 03 00 60 00 70 00 00 00 00 40 00  // "......`.p....@.
    0050: 00 00 5C 5F 53 42 2E 55 41 52 31 00 00 00 00 00  // ..\_SB.UAR1.....
    0060: 00 00 00 46 00 02 10 00 36 00 00 00 00 00 02 80  // ...F....6.......
    0070: 06 00 00 00 16 00 2E 00 00 00 00 03 00 00 00 7D  // ...............}
    0080: 00 00 00 00 00 00 00 03 00 80 5B FD 00 00 00 00  // ..........[.....
    0090: 00 40 00 00 00 40 00 00 5C 5F 53 42 2E 57 44 42  // .@...@..\_SB.WDB
    00A0: 47 00 00 00 00 00 00 00                          // G.......
