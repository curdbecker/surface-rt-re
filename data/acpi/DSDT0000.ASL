// CreatorID=MSFT	CreatorRev=4.0.0
// FileLength=9361	FileChkSum=0x5c

DefinitionBlock("DSDT0000.bin", "DSDT", 0x02, "NVIDIA", "AP30EDK2", 0x00000003)
{
    Scope(\_SB_)
    {
        OperationRegion(APBR, SystemMemory, 0x70000804, 0x4)
        Field(APBR, DWordAcc, NoLock, Preserve)
        {
            CHID, 32
        }
        OperationRegion(NVFM, SystemMemory, 0x82000000, 0x5c)
        Field(NVFM, DWordAcc, NoLock, Preserve)
        {
            Offset(0x8),
            ODAB, 32,
            , 32,
            ODAL, 32,
            , 32,
            FMGB, 32,
            , 32,
            FMGL, 32,
            , 32,
            BPAB, 32,
            , 32,
            BPAL, 32,
            , 32,
            PPIP, 32,
            PPIL, 32,
            PPIR, 32,
            PPIF, 32,
            RTCV, 1,
            Offset(0x50),
            PEDA, 32,
            , 32,
            PEDL, 32
        }
        Method(GEDA, 0x0, NotSerialized)
        {
            Return(PEDA)
        }
        Method(GEDL, 0x0, NotSerialized)
        {
            Return(PEDL)
        }
        Method(GETP, 0x0, NotSerialized)
        {
            Return(ODAB)
        }
        Method(GETL, 0x0, NotSerialized)
        {
            Return(ODAL)
        }
        Method(BPGB, 0x0, NotSerialized)
        {
            Return(BPAB)
        }
        Method(BPGL, 0x0, NotSerialized)
        {
            Return(BPAL)
        }
        OperationRegion(BPMM, SystemMemory, BPGB(), BPGL())
        Field(BPMM, DWordAcc, NoLock, Preserve)
        {
            BPVR, 32,
            BPCU, 32,
            BPBT, 32
        }
        OperationRegion(CLKR, SystemMemory, 0x60006000, 0x1000)
        Field(CLKR, ByteAcc, NoLock, Preserve)
        {
            , 32,
            , 6,
            UAAE, 1,
            UABE, 1,
            GPIE, 1,
            SD2E, 1,
            , 1,
            I2SE, 1,
            I21E, 1,
            , 1,
            SD1E, 1,
            SD4E, 1,
            , 6,
            US1E, 1,
            , 3,
            , 6,
            , 9,
            SP1E, 1,
            , 2,
            SP2E, 1,
            , 1,
            SP3E, 1,
            I24E, 1,
            , 6,
            I22E, 1,
            UACE, 1,
            , 2,
            US2E, 1,
            US3E, 1,
            , 4,
            , 1,
            UADE, 1,
            UAEE, 1,
            I23E, 1,
            SP4E, 1,
            SD3E, 1,
            Offset(0x14),
            , 4,
            KBCE, 1,
            Offset(0x358),
            , 8,
            SP5E, 1,
            SP6E, 1,
            , 19,
            HDAE, 1
        }
        Device(CPU0)
        {
            Name(_HID, "ACPI0007")
            Name(_UID, Zero)
        }
        Device(CPU1)
        {
            Name(_HID, "ACPI0007")
            Name(_UID, One)
        }
        Device(CPU2)
        {
            Name(_HID, "ACPI0007")
            Name(_UID, 0x2)
        }
        Device(CPU3)
        {
            Name(_HID, "ACPI0007")
            Name(_UID, 0x3)
        }
        Method(GCRS, 0x3, NotSerialized)
        {
            Name(RSRC, Buffer(0x17)
            {
	0x86, 0x09, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
	0x89, 0x06, 0x00, 0x01, 0x01, 0x00, 0x00, 0x00, 0x00, 0x79, 0x00
            })
            CreateDWordField(RSRC, 0x4, MBAS)
            CreateDWordField(RSRC, 0x8, MBLE)
            CreateWordField(RSRC, 0x11, INTN)
            MBAS = Arg0
            MBLE = Arg1
            INTN = Arg2
            Return(RSRC)
        }
        Method(UCRS, 0x4, NotSerialized)
        {
            Name(RSRC, Buffer(0x17)
            {
	0x86, 0x09, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
	0x89, 0x06, 0x00, 0x09, 0x01, 0x00, 0x00, 0x00, 0x00, 0x79, 0x00
            })
            CreateDWordField(RSRC, 0x4, MBAS)
            CreateDWordField(RSRC, 0x8, MBLE)
            CreateWordField(RSRC, 0x11, INTN)
            CreateField(RSRC, 0x7b, 0x2, SHRN)
            MBAS = Arg0
            MBLE = Arg1
            INTN = Arg2
            SHRN = Arg3
            Return(RSRC)
        }
        Method(CRSG, 0x3, NotSerialized)
        {
            Name(RSRC, Buffer(0x23)
            {
	0x86, 0x09, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
	0x86, 0x09, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
	0x89, 0x06, 0x00, 0x01, 0x01, 0x00, 0x00, 0x00, 0x00, 0x79, 0x00
            })
            CreateDWordField(RSRC, 0x4, ABAS)
            CreateDWordField(RSRC, 0x8, ABLE)
            CreateDWordField(RSRC, 0x10, BBAS)
            CreateDWordField(RSRC, 0x14, BBLE)
            CreateWordField(RSRC, 0x1d, INTN)
            ABAS = Arg0
            ABLE = Arg1
            BBAS = Arg0 + 0x80
            BBLE = 0x80
            INTN = Arg2
            Return(RSRC)
        }
        Method(CRSD, 0x2, NotSerialized)
        {
            Name(RSRC, Buffer(0xe)
            {
	0x55, 0x00, 0x00, 0x00, 0x00, 0x02, 0x55, 0x01, 0x00, 0x01, 0x00, 0x02,
	0x79, 0x00
            })
            CreateWordField(RSRC, One, REQ1)
            CreateWordField(RSRC, 0x3, CHN1)
            CreateWordField(RSRC, 0x7, REQ2)
            CreateWordField(RSRC, 0x9, CHN2)
            REQ1 = Arg0
            REQ2 = (Arg0 | 0x20)
            CHN1 = Arg1
            CHN2 = (Arg1++)
            Return(RSRC)
        }
        Method(CRS3, 0x5, NotSerialized)
        {
            Local0 = GCRS(Arg0, Arg1, Arg2)
            Local1 = CRSD(Arg3, Arg4)
            Return(ConcatenateResTemplate(Local0, Local1, ))
        }
        Device(DMAC)
        {
            Name(_HID, "NVDA0009")
        }
        Device(TIME)
        {
            Name(_HID, "NVDA000A")
        }
        Device(CACH)
        {
            Name(_HID, "ARMH0310")
        }
        Device(PEPD)
        {
            Method(_HID, 0x0, NotSerialized)
            {
                Return("NVDA0120")
            }
            Method(_CID, 0x0, NotSerialized)
            {
                Return("PNP0D80")
            }
            Name(_CRS, Buffer(0xb)
            {
	0x89, 0x06, 0x00, 0x01, 0x01, 0x4d, 0x00, 0x00, 0x00, 0x79, 0x00
            })
            Method(EMCF, 0x2, NotSerialized)
            {
                Name(BUFA, Buffer(0x4)
                {
	0x00
                })
                CreateDWordField(BUFA, Zero, FREA)
                Local0 = Arg1 + One
                CreateDWordField(Arg0, Local0, FREQ)
                FREA = FREQ
                Return(BUFA)
            }
            Method(GFDS, 0x0, NotSerialized)
            {
                Local3 = (Buffer(One)
                {
	0x00
                })
                Local0 = ^DVFS
                Local1 = (SizeOf(Local0))
                Local1 = Local1 / 0x1cd
                Local2 = Zero
                While(Local1)
                {
                    Local4 = EMCF(Local0, Local2)
                    If(!FROK(Local4))
                    {
                        If((SizeOf(Local3)) < 0x4)
                        {
                            Local3 = Local4
                        }
                        Else
                        {
                            Concatenate(Local3, Local4, Local5)
                            Local3 = Local5
                        }
                    }
                    Local2 = Local2 + 0x1cd
                    Local1--
                }
                Return(Local3)
            }
            Method(FROK, 0x1, NotSerialized)
            {
                Local0 = \_SB_.PLLM()
                Local2 = \_SB_.PLLP()
                Local1 = Local2 / 0x2
                ToInteger(Arg0, Local3)
                If(!(Local3 > Local1))
                {
                    Local5 = Local2 / Local3
                }
                Else
                {
                    If(!(Local0 < Local3))
                    {
                        Local5 = Local0 / Local3
                    }
                    Else
                    {
                        Local5 = Local3 / Local0
                    }
                }
                Return(Local4)
            }
            Method(_DSM, 0x4, NotSerialized)
            {
                If(Arg0 == (Buffer(0x10)
                {
	0x9f, 0xd9, 0x42, 0xe4, 0xe6, 0x77, 0xbf, 0x4e, 0xaf, 0x72, 0xe3, 0xd1,
	0x1c, 0x0d, 0x3d, 0x7d
                }))
                {
                    If(Arg2 == Zero)
                    {
                        If(Arg1 == One)
                        {
                            Local0 = One
                            If(CondRefOf(^DVFS, Local7))
                            {
                                Local0 = Local0 | (One << One)
                                Local0 = Local0 | (One << 0x2)
                            }
                            If(CondRefOf(^THRM, Local6))
                            {
                                Local0 = Local0 | (One << 0x3)
                            }
                            If(CondRefOf(^INFO, Local5))
                            {
                                Local0 = Local0 | (One << 0x4)
                            }
                            Return(Local0)
                        }
                    }
                    If(Arg2 == One)
                    {
                        Return(^GFDS())
                    }
                    If(Arg2 == 0x2)
                    {
                        Return(^DVFS)
                    }
                    If(Arg2 == 0x3)
                    {
                        Return(^THRM)
                    }
                    If(Arg2 == 0x4)
                    {
                        Return(^INFO)
                    }
                }
                Return(Buffer(One)
                {
	0x00
                })
            }
            Name(ROST, Zero)
            Method(NPUR, 0x1, NotSerialized)
            {
                \_SB_.PARG._PUR[One] = Arg0
                Notify(\_SB_.PARG, 0x80)
            }
        }
        Field(CLKR, ByteAcc, NoLock, Preserve)
        {
            Offset(0x50),
            , 28,
            OSCR, 4,
            Offset(0x90),
            DVMM, 5,
            , 3,
            DVNM, 10,
            , 2,
            DVPM, 3,
            , 8,
            BYPM, 1,
            Offset(0xa0),
            DVMP, 5,
            , 3,
            DVNP, 10,
            , 2,
            DVPP, 3,
            , 5,
            BOVP, 1,
            , 2,
            BYPP, 1
        }
        Method(GREF, 0x0, NotSerialized)
        {
            If(OSCR == 0x8)
            {
                Return(0x2ee0)
            }
            If(OSCR == Zero)
            {
                Return(0x32c8)
            }
            If(OSCR == One)
            {
                Return(0x41a0)
            }
            If(OSCR == 0x4)
            {
                Return(0x4b00)
            }
            If(OSCR == 0xc)
            {
                Return(0x6590)
            }
            If(OSCR == 0x5)
            {
                Return(0x9600)
            }
            If(OSCR == 0x9)
            {
                Return(0xbb80)
            }
            Return(Zero)
        }
        Method(GPLL, 0x4, NotSerialized)
        {
            Local0 = GREF()
            If(!Arg3)
            {
                Local0 = Local0 * Arg0
                Local1 = Local0 / Arg1
                Local0 = Local1 >> Arg2
            }
            Return(Local0)
        }
        Method(PLLM, 0x0, NotSerialized)
        {
            Return(GPLL(DVNM, DVMM, DVPM, BYPM))
        }
        Method(PLLP, 0x0, NotSerialized)
        {
            If(!BOVP)
            {
                Return(0x34bc0)
            }
            Else
            {
                Return(GPLL(DVNP, DVMP, DVPP, BYPP))
            }
        }
        Device(PARG)
        {
            Name(_HID, "ACPI000C")
            Name(_PUR, Package(0x2)
            {
                One,
                Zero
            })
            Method(_OST, 0x3, NotSerialized)
            {
                \_SB_.PEPD.ROST = Arg2
                Notify(\_SB_.PEPD, 0xc0)
            }
        }
        Device(MCDV)
        {
            Method(_HID, 0x0, NotSerialized)
            {
                Return("NVDA010E")
            }
            Name(_CRS, Buffer(0x23)
            {
	0x86, 0x09, 0x00, 0x01, 0x00, 0xf0, 0x00, 0x70, 0x00, 0x10, 0x00, 0x00,
	0x86, 0x09, 0x00, 0x01, 0x00, 0xc0, 0x00, 0x60, 0x00, 0x02, 0x00, 0x00,
	0x89, 0x06, 0x00, 0x01, 0x01, 0x6d, 0x00, 0x00, 0x00, 0x79, 0x00
            })
            Name(_HRV, Zero)
            Method(_INI, 0x0, NotSerialized)
            {
                ^_HRV = CHID
            }
        }
        Device(KBCD)
        {
            Method(_HID, 0x0, NotSerialized)
            {
                Return("NVDA000C")
            }
            Method(_CRS, 0x0, NotSerialized)
            {
                Local0 = UCRS(0x7000e200, 0x100, 0x75, 0x2)
                If(CondRefOf(^CRSA, Local7))
                {
                    ConcatenateResTemplate(Local0, ^CRSA, Local1)
                    Local0 = Local1
                }
                Return(Local0)
            }
            Name(STAF, Zero)
            Method(_STA, 0x0, NotSerialized)
            {
                If(^STAF)
                {
                    Return(0xf)
                }
                If(^^KBCE)
                {
                    ^STAF = One
                    Return(0xf)
                }
                Return(Zero)
            }
        }
        Device(UAR1)
        {
            Method(_HID, 0x0, NotSerialized)
            {
                Return("NVDA0100")
            }
            Name(_UID, Zero)
            Method(_CRS, 0x0, NotSerialized)
            {
                Return(CRS3(0x70006000, 0x40, 0x44, 0x8, Zero))
            }
            Name(STAF, Zero)
            Method(_STA, 0x0, NotSerialized)
            {
                If(CondRefOf(^UDP_, Local7))
                {
                    If(^UDP_)
                    {
                        Return(Zero)
                    }
                }
                If(^STAF)
                {
                    Return(0xf)
                }
                If(!^^UAAE)
                {
                    ^STAF = One
                    Return(0xf)
                }
                Return(Zero)
            }
            Name(_DEP, Package(0x1)
            {
                \_SB_.PEPD
            })
        }
        Device(UAR2)
        {
            Method(_HID, 0x0, NotSerialized)
            {
                Return("NVDA0100")
            }
            Name(_UID, One)
            Method(_CRS, 0x0, NotSerialized)
            {
                Return(CRS3(0x70006040, 0x40, 0x45, 0x9, 0x2))
            }
            Name(STAF, Zero)
            Method(_STA, 0x0, NotSerialized)
            {
                If(CondRefOf(^UDP_, Local7))
                {
                    If(^UDP_)
                    {
                        Return(Zero)
                    }
                }
                If(^STAF)
                {
                    Return(0xf)
                }
                If(!^^UABE)
                {
                    ^STAF = One
                    Return(0xf)
                }
                Return(Zero)
            }
            Name(_DEP, Package(0x1)
            {
                \_SB_.PEPD
            })
        }
        Device(UAR3)
        {
            Method(_HID, 0x0, NotSerialized)
            {
                Return("NVDA0100")
            }
            Name(_UID, 0x2)
            Method(_CRS, 0x0, NotSerialized)
            {
                Return(CRS3(0x70006200, 0x40, 0x4e, 0xa, 0x4))
            }
            Name(STAF, Zero)
            Method(_STA, 0x0, NotSerialized)
            {
                If(CondRefOf(^UDP_, Local7))
                {
                    If(^UDP_)
                    {
                        Return(Zero)
                    }
                }
                If(^STAF)
                {
                    Return(0xf)
                }
                If(!^^UACE)
                {
                    ^STAF = One
                    Return(0xf)
                }
                Return(Zero)
            }
            Name(_DEP, Package(0x1)
            {
                \_SB_.PEPD
            })
        }
        Device(UAR4)
        {
            Method(_HID, 0x0, NotSerialized)
            {
                Return("NVDA0100")
            }
            Name(_UID, 0x3)
            Method(_CRS, 0x0, NotSerialized)
            {
                Return(CRS3(0x70006300, 0x40, 0x7a, 0x13, 0x6))
            }
            Name(STAF, Zero)
            Method(_STA, 0x0, NotSerialized)
            {
                If(CondRefOf(^UDP_, Local7))
                {
                    If(^UDP_)
                    {
                        Return(Zero)
                    }
                }
                If(^STAF)
                {
                    Return(0xf)
                }
                If(!^^UADE)
                {
                    ^STAF = One
                    Return(0xf)
                }
                Return(Zero)
            }
            Name(_DEP, Package(0x1)
            {
                \_SB_.PEPD
            })
        }
        Device(UAR5)
        {
            Method(_HID, 0x0, NotSerialized)
            {
                Return("NVDA0100")
            }
            Name(_UID, 0x4)
            Method(_CRS, 0x0, NotSerialized)
            {
                Return(CRS3(0x70006400, 0x40, 0x7b, 0x14, 0x8))
            }
            Name(STAF, Zero)
            Method(_STA, 0x0, NotSerialized)
            {
                If(CondRefOf(^UDP_, Local7))
                {
                    If(^UDP_)
                    {
                        Return(Zero)
                    }
                }
                If(^STAF)
                {
                    Return(0xf)
                }
                If(!^^UAEE)
                {
                    ^STAF = One
                    Return(0xf)
                }
                Return(Zero)
            }
            Name(_DEP, Package(0x1)
            {
                \_SB_.PEPD
            })
        }
        OperationRegion(GPOP, SystemMemory, 0x6000d000, 0x800)
        Field(GPOP, DWordAcc, NoLock, Preserve)
        {
            Offset(0x38),
            SCI1, 8,
            Offset(0x88),
            SCF1, 16,
            Offset(0x98),
            SCE1, 16,
            Offset(0xa8),
            SCO1, 16,
            Offset(0x43c),
            SCI2, 8,
            Offset(0x48c),
            SCF2, 16,
            Offset(0x49c),
            SCE2, 16,
            Offset(0x4ac),
            SCO2, 16,
            Offset(0x534),
            SCI4, 8,
            Offset(0x584),
            SCF4, 16,
            Offset(0x594),
            SCE4, 16,
            Offset(0x5a4),
            SCO4, 16,
            Offset(0x634),
            SCI5, 8,
            Offset(0x63c),
            SCI3, 8,
            Offset(0x684),
            SCF5, 16,
            Offset(0x68c),
            SCF3, 16,
            Offset(0x694),
            SCE5, 16,
            Offset(0x69c),
            SCE3, 16,
            Offset(0x6a4),
            SCO5, 16,
            Offset(0x6ac),
            SCO3, 16
        }
        Method(I2CR, 0x5, NotSerialized)
        {
            Local0 = 0xa
            Arg0 = (0x303 << Arg4)
            Arg1 = (0x303 << Arg4)
            Stall(0xa)
            While(Local0)
            {
                If((DerefOf(Arg3)) & (0x2 << Arg4))
                {
                    Break
                }
                Else
                {
                    Arg2 = (0x100 << Arg4)
                    Stall(0x5)
                    Arg2 = (0x101 << Arg4)
                    Stall(0x5)
                    Arg2 = (0x202 << Arg4)
                    Stall(0x5)
                }
                Local0--
            }
            Arg1 = (0x300 << Arg4)
            Arg0 = (0x300 << Arg4)
        }
        Device(I2C1)
        {
            Method(_HID, 0x0, NotSerialized)
            {
                Return("NVDA0101")
            }
            Name(_UID, One)
            Name(AVBL, Zero)
            Method(_REG, 0x2, NotSerialized)
            {
                If(Arg0 == 0x9)
                {
                    AVBL = Arg1
                }
            }
            Method(_CRS, 0x0, NotSerialized)
            {
                Return(GCRS(0x7000c000, 0x100, 0x46))
            }
            Name(_DEP, Package(0x1)
            {
                \_SB_.PEPD
            })
            Method(RST_, 0x0, NotSerialized)
            {
                \_SB_.I2CR(RefOf(SCF1), RefOf(SCE1), RefOf(SCO1), RefOf(SCI1), 0x4)
            }
        }
        Device(I2C2)
        {
            Method(_HID, 0x0, NotSerialized)
            {
                Return("NVDA0101")
            }
            Name(_UID, 0x2)
            Name(AVBL, Zero)
            Method(_REG, 0x2, NotSerialized)
            {
                If(Arg0 == 0x9)
                {
                    AVBL = Arg1
                }
            }
            Method(_CRS, 0x0, NotSerialized)
            {
                Return(GCRS(0x7000c400, 0x100, 0x74))
            }
            Name(_DEP, Package(0x1)
            {
                \_SB_.PEPD
            })
            Method(RST_, 0x0, NotSerialized)
            {
                \_SB_.I2CR(RefOf(SCF2), RefOf(SCE2), RefOf(SCO2), RefOf(SCI2), 0x5)
            }
        }
        Device(I2C3)
        {
            Method(_HID, 0x0, NotSerialized)
            {
                Return("NVDA0101")
            }
            Name(_UID, 0x3)
            Name(AVBL, Zero)
            Method(_REG, 0x2, NotSerialized)
            {
                If(Arg0 == 0x9)
                {
                    AVBL = Arg1
                }
            }
            Method(_CRS, 0x0, NotSerialized)
            {
                Return(GCRS(0x7000c500, 0x100, 0x7c))
            }
            Name(_DEP, Package(0x1)
            {
                \_SB_.PEPD
            })
            Method(RST_, 0x0, NotSerialized)
            {
                \_SB_.I2CR(RefOf(SCF3), RefOf(SCE3), RefOf(SCO3), RefOf(SCI3), One)
            }
        }
        Device(I2C4)
        {
            Method(_HID, 0x0, NotSerialized)
            {
                Return("NVDA0101")
            }
            Name(_UID, 0x4)
            Name(AVBL, Zero)
            Method(_REG, 0x2, NotSerialized)
            {
                If(Arg0 == 0x9)
                {
                    AVBL = Arg1
                }
            }
            Method(_CRS, 0x0, NotSerialized)
            {
                Return(GCRS(0x7000c700, 0x100, 0x98))
            }
            Name(_DEP, Package(0x1)
            {
                \_SB_.PEPD
            })
            Method(RST_, 0x0, NotSerialized)
            {
                \_SB_.I2CR(RefOf(SCF4), RefOf(SCE4), RefOf(SCO4), RefOf(SCI4), 0x4)
            }
        }
        Device(I2C5)
        {
            Method(_HID, 0x0, NotSerialized)
            {
                Return("NVDA0101")
            }
            Name(_UID, 0x5)
            Name(AVBL, Zero)
            Method(_REG, 0x2, NotSerialized)
            {
                If(Arg0 == 0x9)
                {
                    AVBL = Arg1
                }
            }
            Method(_CRS, 0x0, NotSerialized)
            {
                Return(GCRS(0x7000d000, 0x100, 0x55))
            }
            Name(_DEP, Package(0x1)
            {
                \_SB_.PEPD
            })
            Method(RST_, 0x0, NotSerialized)
            {
                \_SB_.I2CR(RefOf(SCF5), RefOf(SCE5), RefOf(SCO5), RefOf(SCI5), 0x6)
            }
        }
        Device(USB1)
        {
            OperationRegion(USCR, SystemMemory, 0x7d000000, 0x4000)
            Field(USCR, WordAcc, NoLock, Preserve)
            {
                UNID, 16,
                Offset(0x154),
                TXPR, 32,
                Offset(0x174),
                SCPR, 32,
                Offset(0x1f8),
                UMOD, 32
            }
            Method(_HID, 0x0, NotSerialized)
            {
                Return("NVDA0103")
            }
            Name(_CID, "ACPI\\PNP0D20")
            Name(_HRV, 0x2)
            Name(_UID, Zero)
            Method(_CRS, 0x0, NotSerialized)
            {
                Local0 = 0x7d000000 + 0x100
                Local1 = 0x4000 - 0x100
                Return(UCRS(Local0, Local1, 0x34, 0x3))
            }
            Name(VAR0, Zero)
            Name(VAR1, Zero)
            Name(VAR2, Zero)
            Name(STAF, Zero)
            Method(_STA, 0x0, NotSerialized)
            {
                If(^STAF)
                {
                    If(^VAR0 == 0x3)
                    {
                        Return(0xf)
                    }
                    Else
                    {
                        Return(Zero)
                    }
                }
                If(!^^US1E)
                {
                    ^STAF = One
                    VAR0 = ^UMOD
                    If(^UMOD == 0x3)
                    {
                        Return(0xf)
                    }
                    Else
                    {
                        Return(Zero)
                    }
                }
                Return(Zero)
            }
            Method(_INI, 0x0, NotSerialized)
            {
                VAR0 = ^UMOD
                VAR1 = ^SCPR
                VAR2 = ^TXPR
            }
            Method(_UBF, 0x0, NotSerialized)
            {
                ^UMOD = VAR0
                ^SCPR = VAR1
                ^TXPR = VAR2
            }
            Method(_DSM, 0x4, NotSerialized)
            {
                If(Arg0 == (Buffer(0x10)
                {
	0x85, 0xe3, 0x2e, 0xce, 0xe6, 0x00, 0xcb, 0x48, 0x9f, 0x05, 0x2e, 0xdb,
	0x92, 0x7c, 0x48, 0x99
                }))
                {
                    If(Arg2 == Zero)
                    {
                        If(Arg1 == Zero)
                        {
                            Return(Buffer(One)
                            {
	0x03
                            })
                        }
                    }
                    If(Arg2 == One)
                    {
                        ^_UBF()
                    }
                }
                Else
                {
                    Return(Buffer(One)
                    {
	0x00
                    })
                }
            }
            Name(_DEP, Package(0x1)
            {
                \_SB_.PEPD
            })
            Name(_S0W, 0x3)
            Name(_S4W, 0x3)
        }
        Device(WDBG)
        {
            OperationRegion(USCR, SystemMemory, 0x7d000000, 0x4000)
            Field(USCR, WordAcc, NoLock, Preserve)
            {
                UNID, 16,
                Offset(0x154),
                TXPR, 32,
                Offset(0x174),
                SCPR, 32,
                Offset(0x1f8),
                UMOD, 32
            }
            Method(_HID, 0x0, NotSerialized)
            {
                Return("NVDA0102")
            }
            Name(_UID, Zero)
            Method(_CRS, 0x0, NotSerialized)
            {
                Local0 = 0x7d000000 + 0x100
                Local1 = 0x4000 - 0x100
                Return(UCRS(Local0, Local1, 0x34, One))
            }
            Name(VAR0, Zero)
            Name(VAR1, Zero)
            Name(VAR2, Zero)
            Name(STAF, Zero)
            Method(_STA, 0x0, NotSerialized)
            {
                If(^STAF)
                {
                    If(^VAR0 == 0x3)
                    {
                        Return(Zero)
                    }
                    Else
                    {
                        Return(0xf)
                    }
                }
                If(!^^US1E)
                {
                    ^STAF = One
                    VAR0 = ^UMOD
                    If(^UMOD == 0x3)
                    {
                        Return(Zero)
                    }
                    Else
                    {
                        Return(0xf)
                    }
                }
                Return(Zero)
            }
            Method(_INI, 0x0, NotSerialized)
            {
                VAR0 = ^UMOD
                VAR1 = ^SCPR
                VAR2 = ^TXPR
            }
            Method(_UBF, 0x0, NotSerialized)
            {
                ^UMOD = VAR0
                ^SCPR = VAR1
                ^TXPR = VAR2
            }
            Method(_DSM, 0x4, NotSerialized)
            {
                If(Arg0 == (Buffer(0x10)
                {
	0x85, 0xe3, 0x2e, 0xce, 0xe6, 0x00, 0xcb, 0x48, 0x9f, 0x05, 0x2e, 0xdb,
	0x92, 0x7c, 0x48, 0x99
                }))
                {
                    If(Arg2 == Zero)
                    {
                        If(Arg1 == Zero)
                        {
                            Return(Buffer(One)
                            {
	0x03
                            })
                        }
                    }
                    If(Arg2 == One)
                    {
                        ^_UBF()
                    }
                }
                Else
                {
                    Return(Buffer(One)
                    {
	0x00
                    })
                }
            }
            Name(_DEP, Package(0x1)
            {
                \_SB_.PEPD
            })
            Name(_S0W, 0x3)
        }
        Device(USB2)
        {
            Method(_HID, 0x0, NotSerialized)
            {
                Return("NVDA0103")
            }
            Name(_CID, "ACPI\\PNP0D20")
            Name(_HRV, 0x2)
            Name(_UID, One)
            OperationRegion(USCR, SystemMemory, 0x7d004000, 0x4000)
            Field(USCR, WordAcc, NoLock, Preserve)
            {
                UNID, 16,
                Offset(0x154),
                TXPR, 32,
                Offset(0x174),
                SCPR, 32,
                Offset(0x1f8),
                UMOD, 32
            }
            Method(_CRS, 0x0, NotSerialized)
            {
                Local0 = 0x7d004000 + 0x100
                Local1 = 0x4000 - 0x100
                Return(UCRS(Local0, Local1, 0x35, 0x3))
            }
            Name(STAF, Zero)
            Method(_STA, 0x0, NotSerialized)
            {
                If(^STAF)
                {
                    Return(0xf)
                }
                If(!^^US2E)
                {
                    ^STAF = One
                    Return(0xf)
                }
                Return(Zero)
            }
            Name(VAR0, Zero)
            Name(VAR1, Zero)
            Name(VAR2, Zero)
            Method(_INI, 0x0, NotSerialized)
            {
                VAR0 = ^UMOD
                VAR1 = ^SCPR
                VAR2 = ^TXPR
            }
            Method(_UBF, 0x0, NotSerialized)
            {
                ^UMOD = VAR0
                ^SCPR = VAR1
                ^TXPR = VAR2
            }
            Method(_DSM, 0x4, NotSerialized)
            {
                If(Arg0 == (Buffer(0x10)
                {
	0x85, 0xe3, 0x2e, 0xce, 0xe6, 0x00, 0xcb, 0x48, 0x9f, 0x05, 0x2e, 0xdb,
	0x92, 0x7c, 0x48, 0x99
                }))
                {
                    If(Arg2 == Zero)
                    {
                        If(Arg1 == Zero)
                        {
                            Return(Buffer(One)
                            {
	0x03
                            })
                        }
                    }
                    If(Arg2 == One)
                    {
                        ^_UBF()
                    }
                }
                Else
                {
                    Return(Buffer(One)
                    {
	0x00
                    })
                }
            }
            Name(_DEP, Package(0x1)
            {
                \_SB_.PEPD
            })
            Name(_S0W, 0x3)
            Name(_S4W, 0x3)
        }
        Device(USB3)
        {
            Method(_HID, 0x0, NotSerialized)
            {
                Return("NVDA0103")
            }
            Name(_CID, "ACPI\\PNP0D20")
            Name(_HRV, 0x2)
            Name(_UID, 0x2)
            OperationRegion(USCR, SystemMemory, 0x7d008000, 0x4000)
            Field(USCR, WordAcc, NoLock, Preserve)
            {
                UNID, 16,
                Offset(0x154),
                TXPR, 32,
                Offset(0x174),
                SCPR, 32,
                Offset(0x1f8),
                UMOD, 32
            }
            Method(_CRS, 0x0, NotSerialized)
            {
                Local0 = 0x7d008000 + 0x100
                Local1 = 0x4000 - 0x100
                Return(UCRS(Local0, Local1, 0x81, 0x3))
            }
            Name(STAF, Zero)
            Method(_STA, 0x0, NotSerialized)
            {
                If(^STAF)
                {
                    Return(0xf)
                }
                If(!^^US3E)
                {
                    ^STAF = One
                    Return(0xf)
                }
                Return(Zero)
            }
            Name(VAR0, Zero)
            Name(VAR1, Zero)
            Name(VAR2, Zero)
            Method(_INI, 0x0, NotSerialized)
            {
                VAR0 = UMOD
                VAR1 = SCPR
                VAR2 = TXPR
            }
            Method(_UBF, 0x0, NotSerialized)
            {
                UMOD = VAR0
                SCPR = VAR1
                TXPR = VAR2
            }
            Method(_DSM, 0x4, NotSerialized)
            {
                If(Arg0 == (Buffer(0x10)
                {
	0x85, 0xe3, 0x2e, 0xce, 0xe6, 0x00, 0xcb, 0x48, 0x9f, 0x05, 0x2e, 0xdb,
	0x92, 0x7c, 0x48, 0x99
                }))
                {
                    If(Arg2 == Zero)
                    {
                        If(Arg1 == Zero)
                        {
                            Return(Buffer(One)
                            {
	0x03
                            })
                        }
                    }
                    If(Arg2 == One)
                    {
                        ^_UBF()
                    }
                }
                Else
                {
                    Return(Buffer(One)
                    {
	0x00
                    })
                }
            }
            Name(_DEP, Package(0x1)
            {
                \_SB_.PEPD
            })
            Name(_S0W, 0x3)
            Name(_S4W, 0x3)
        }
        Device(NVSE)
        {
            Method(_HID, 0x0, NotSerialized)
            {
                Return("NVDA010D")
            }
            Name(_UID, Zero)
            Name(SBUF, Buffer(0x43)
            {
	0x86, 0x09, 0x00, 0x01, 0x00, 0x10, 0x01, 0x60, 0x00, 0x10, 0x00, 0x00,
	0x86, 0x09, 0x00, 0x01, 0x00, 0xb0, 0x01, 0x60, 0x00, 0x10, 0x00, 0x00,
	0x86, 0x09, 0x00, 0x01, 0x00, 0x20, 0x01, 0x70, 0x00, 0x20, 0x00, 0x00,
	0x86, 0x09, 0x00, 0x01, 0x00, 0x20, 0x00, 0x60, 0x00, 0x10, 0x00, 0x00,
	0x89, 0x0e, 0x00, 0x01, 0x03, 0x2a, 0x00, 0x00, 0x00, 0x2b, 0x00, 0x00,
	0x00, 0x5a, 0x00, 0x00, 0x00, 0x79, 0x00
            })
            Method(_CRS, 0x0, NotSerialized)
            {
                Local0 = ^SBUF
                Return(Local0)
            }
            Name(_DEP, Package(0x1)
            {
                \_SB_.PEPD
            })
        }
        Device(NVTZ)
        {
            Method(_HID, 0x0, NotSerialized)
            {
                Return("NVDA0110")
            }
            Name(_UID, Zero)
            Name(_DEP, Package(0x1)
            {
                \_SB_.SDM4.STOR.EMMC
            })
        }
        Device(GFXC)
        {
            Method(_HID, 0x0, NotSerialized)
            {
                Return("NVDA0105")
            }
            Name(_UID, Zero)
            Name(_CLS, 0x3000000000000)
            Method(_CRS, 0x0, NotSerialized)
            {
                Name(VBUF, Buffer(0x8c)
                {
	0x86, 0x09, 0x00, 0x01, 0x00, 0x00, 0x00, 0x50, 0x00, 0x00, 0x44, 0x04,
	0x86, 0x09, 0x00, 0x01, 0x00, 0x70, 0x00, 0x60, 0x00, 0x10, 0x00, 0x00,
	0x86, 0x09, 0x00, 0x01, 0x00, 0x10, 0x00, 0x60, 0x00, 0x10, 0x00, 0x00,
	0x86, 0x09, 0x00, 0x01, 0x00, 0xf0, 0x00, 0x60, 0x00, 0x10, 0x00, 0x00,
	0x86, 0x09, 0x00, 0x01, 0x00, 0x00, 0x00, 0xb0, 0x00, 0x00, 0x00, 0x04,
	0x86, 0x09, 0x00, 0x01, 0x00, 0xa0, 0x00, 0x70, 0x00, 0x01, 0x00, 0x00,
	0x86, 0x09, 0x00, 0x01, 0x60, 0x50, 0x00, 0x60, 0x08, 0x00, 0x00, 0x00,
	0x89, 0x06, 0x00, 0x01, 0x01, 0x24, 0x00, 0x00, 0x00, 0x89, 0x06, 0x00,
	0x01, 0x01, 0x61, 0x00, 0x00, 0x00, 0x89, 0x06, 0x00, 0x01, 0x01, 0x63,
	0x00, 0x00, 0x00, 0x89, 0x06, 0x00, 0x01, 0x01, 0x68, 0x00, 0x00, 0x00,
	0x89, 0x06, 0x00, 0x01, 0x01, 0x69, 0x00, 0x00, 0x00, 0x89, 0x06, 0x00,
	0x01, 0x01, 0x6a, 0x00, 0x00, 0x00, 0x79, 0x00
                })
                CreateDWordField(VBUF, 0x34, GCBA)
                CreateDWordField(VBUF, 0x38, GCLE)
                GCBA = \_SB_.FMGB
                GCLE = \_SB_.FMGL
                Local0 = VBUF
                If(CondRefOf(^CRSA, Local7))
                {
                    ConcatenateResTemplate(VBUF, ^CRSA, Local0)
                }
                Return(Local0)
            }
            Method(_STA, 0x0, NotSerialized)
            {
                Return(0xf)
            }
            Method(_DSM, 0x4, NotSerialized)
            {
                If(Arg0 == (Buffer(0x10)
                {
	0x75, 0x0b, 0xa5, 0xd4, 0xc7, 0x65, 0xf7, 0x46, 0xbf, 0xb7, 0x41, 0x51,
	0x4c, 0xea, 0x02, 0x44
                }))
                {
                    While(One)
                    {
                        Name(_T_0, 0x0)
                        _T_0 = Arg2
                        If(_T_0 == Zero)
                        {
                            Local0 = Zero
                            Local0 = Local0 | (One << Zero)
                            Local0 = Local0 | (One << 0x10)
                            If(CondRefOf(^MDTL, Local7))
                            {
                                If(\_SB_.GFXC.MDTL == One)
                                {
                                    Local0 = Local0 | (One << 0x6)
                                    Local0 = Local0 | (One << 0x5)
                                }
                            }
                            If(CondRefOf(^BKLP, Local6))
                            {
                                Local0 = Local0 | (One << 0x14)
                            }
                            Return(Local0)
                        }
                        Else
                        {
                            If(_T_0 == 0x10)
                            {
                                Return(GOBT(Arg3))
                            }
                            Else
                            {
                                If(_T_0 == 0x14)
                                {
                                    Return(^BKLP)
                                }
                                Else
                                {
                                    If(_T_0 == 0x5)
                                    {
                                        Debug = "NBCI_DISPLAYSTATUS"
                                        Return(DSMS(Arg3))
                                    }
                                    Else
                                    {
                                        If(_T_0 == 0x6)
                                        {
                                            Debug = "NBCI_MDTL"
                                            Local0 = GDOD(\_SB_.GFXC._DOD)
                                            Return(GGMP(Local0))
                                        }
                                        Else
                                        {
                                            Return(0x80000002)
                                        }
                                    }
                                }
                            }
                        }
                        Break
                    }
                }
                Return(Buffer(One)
                {
	0x00
                })
            }
            Method(GOBT, 0x1, NotSerialized)
            {
                CreateWordField(Arg0, 0x2, USRG)
                CreateWordField(Arg0, Zero, OIND)
                Name(NBBU, Buffer(0x10)
                {
	0x00
                })
                CreateWordField(NBBU, 0x8, NBB1)
                CreateDWordField(NBBU, 0xa, NBB2)
                If(USRG == 0x5447)
                {
                    Name(TBUF, Buffer(0x8)
                    {
	0x00
                    })
                    CreateDWordField(TBUF, Zero, IDBU)
                    CreateDWordField(TBUF, Zero, FLG0)
                    NBB1 = 0x5447
                    IDBU = \_SB_.CHID
                    If(CondRefOf(^TGF0, Local7))
                    {
                        FLG0 = ^TGF0
                    }
                    NBB2 = 0x8 + (SizeOf(NBBU))
                    Return(Concatenate(NBBU, TBUF, ))
                }
                If(USRG == 0x5444)
                {
                    If(CondRefOf(^DCBB, Local7))
                    {
                        NBB1 = 0x5444
                        Local0 = ^DCBB
                        NBB2 = (SizeOf(Local0)) + (SizeOf(NBBU))
                        Return(Concatenate(NBBU, Local0, ))
                    }
                }
                If(USRG == 0x5443)
                {
                    If(CondRefOf(^TCBB, Local7))
                    {
                        NBB1 = 0x5443
                        Local0 = ^TCBB
                        NBB2 = (SizeOf(Local0)) + (SizeOf(NBBU))
                        Return(Concatenate(NBBU, Local0, ))
                    }
                }
                If(USRG == 0x5450)
                {
                    If(CondRefOf(^TPBB, Local7))
                    {
                        NBB1 = 0x5450
                        Local0 = ^TPBB
                        NBB2 = (SizeOf(Local0)) + (SizeOf(NBBU))
                        Return(Concatenate(NBBU, Local0, ))
                    }
                }
                If(USRG == 0x4452)
                {
                    If(OIND == Zero)
                    {
                        If(CondRefOf(^DRBB, Local7))
                        {
                            Return(^DRBB)
                        }
                        Else
                        {
                            Return(Buffer(0xc5)
                            {
	0xf6, 0x47, 0xef, 0x8b, 0xab, 0x56, 0x72, 0xfd, 0x52, 0x44, 0xc5, 0x00,
	0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0xde, 0x10, 0x00, 0x00,
	0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x09, 0x00, 0x00, 0x00,
	0x00, 0x00, 0x34, 0x00, 0x00, 0x00, 0x01, 0x00, 0x47, 0x00, 0x00, 0x00,
	0x02, 0x00, 0x45, 0x00, 0x00, 0x00, 0x03, 0x00, 0x75, 0x00, 0x00, 0x00,
	0x04, 0x00, 0x73, 0x00, 0x00, 0x00, 0x05, 0x00, 0x71, 0x00, 0x00, 0x00,
	0x06, 0x00, 0x6f, 0x00, 0x00, 0x00, 0x07, 0x00, 0x6d, 0x00, 0x00, 0x00,
	0x08, 0x00, 0x6b, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0xd9, 0x1c,
	0x04, 0x00, 0x00, 0x00, 0x02, 0x00, 0x00, 0x00, 0x41, 0x5d, 0xc9, 0x00,
	0x01, 0x24, 0x2e, 0x00, 0x02, 0x00, 0xff, 0x00, 0x00, 0x00, 0x00, 0x01,
	0x00, 0x00, 0x00, 0xd9, 0x1c, 0x04, 0x00, 0x00, 0x00, 0x0a, 0x00, 0x00,
	0x00, 0xf0, 0x9b, 0x88, 0x00, 0xf0, 0x35, 0xd1, 0x00, 0x60, 0x4f, 0x4f,
	0x01, 0x90, 0xd2, 0xc6, 0x02, 0x50, 0x08, 0xd3, 0x03, 0xc0, 0xe0, 0x9e,
	0x00, 0xa0, 0x06, 0xb6, 0x00, 0x80, 0xf5, 0x91, 0x00, 0x40, 0xbd, 0x6b,
	0x4b, 0x60, 0x9d, 0x44, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
	0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
	0x00, 0x00, 0x00, 0x00, 0x00
                            })
                        }
                    }
                }
                Return(0x80000002)
            }
            Method(GDOD, 0x1, NotSerialized)
            {
                Name(DOD1, Package(One)
                {
                })
                Name(DOD2, Package(0x2)
                {
                })
                Name(DOD3, Package(0x3)
                {
                })
                Local0 = (SizeOf(Arg0))
                Local1 = Zero
                Local2 = Zero
                While(Local1 < Local0)
                {
                    If(Local2 < 0x3)
                    {
                        If((DerefOf(Arg0[Local1])) == 0x80007330)
                        {
                            DOD3[Local2] = (DerefOf(Arg0[Local1]))
                            Local2++
                        }
                        If((DerefOf(Arg0[Local1])) == 0x80000100)
                        {
                            DOD3[Local2] = (DerefOf(Arg0[Local1]))
                            Local2++
                        }
                        If((DerefOf(Arg0[Local1])) == 0x110)
                        {
                            DOD3[Local2] = (DerefOf(Arg0[Local1]))
                            Local2++
                        }
                    }
                    Local1++
                }
                If(Local2 == One)
                {
                    DOD1[Zero] = (DerefOf(DOD3[Zero]))
                    Return(DOD1)
                }
                If(Local2 == 0x2)
                {
                    DOD2[Zero] = (DerefOf(DOD3[Zero]))
                    DOD2[One] = (DerefOf(DOD3[One]))
                    Return(DOD2)
                }
                Return(DOD3)
            }
            Method(CMES, 0x1, NotSerialized)
            {
                Local0 = Arg0
                Local1 = Local0 * 0x2
                Local2 = Zero
                Local0--
                While(Local0)
                {
                    Local2 = Local0 + Local2
                    Local0--
                }
                Local2 = Local2 * 0x3
                Return(Local1 + Local2)
            }
            Name(TPK1, Package(0x2)
            {
            })
            Name(TPK2, Package(0x7)
            {
            })
            Name(TPK3, Package(0xf)
            {
            })
            Name(TPK4, Package(0x1a)
            {
            })
            Name(TPK5, Package(0x28)
            {
            })
            Name(TPK6, Package(0x39)
            {
            })
            Name(TPK7, Package(0x4d)
            {
            })
            Name(TPK8, Package(0x64)
            {
            })
            Method(GGMP, 0x1, NotSerialized)
            {
                Local0 = (SizeOf(Arg0))
                If(Local0 > 0x8)
                {
                    Local0 = 0x8
                }
                Local0 = CMES(Local0)
                If(Local0 == 0x2)
                {
                    Local6 = ^TPK1
                }
                If(Local0 == 0x7)
                {
                    Local6 = ^TPK2
                }
                If(Local0 == 0xf)
                {
                    Local6 = ^TPK3
                }
                If(Local0 == 0x1a)
                {
                    Local6 = ^TPK4
                }
                If(Local0 == 0x28)
                {
                    Local6 = ^TPK5
                }
                If(Local0 == 0x39)
                {
                    Local6 = ^TPK6
                }
                If(Local0 == 0x4d)
                {
                    Local6 = ^TPK7
                }
                If(Local0 == 0x64)
                {
                    Local6 = ^TPK8
                }
                Local0 = Zero
                Local1 = Zero
                Local2 = (SizeOf(Arg0))
                While(Local2)
                {
                    Local6[Local1] = (DerefOf(Arg0[Local0]))
                    Local1++
                    Local6[Local1] = 0x2c
                    Local1++
                    Local0++
                    Local2--
                }
                Local2 = (SizeOf(Arg0))
                Local2--
                Local0 = Zero
                While(Local2)
                {
                    Local3 = Local0
                    Local4 = Local2
                    While(Local4)
                    {
                        Local6[Local1] = (DerefOf(Arg0[Local0]))
                        Local1++
                        Local3++
                        Local6[Local1] = (DerefOf(Arg0[Local3]))
                        Local1++
                        Local6[Local1] = 0x2c
                        Local1++
                        Local4--
                    }
                    Local0++
                    Local2--
                }
                Return(Local6)
            }
            Name(CTOI, Zero)
            Method(DSMS, 0x1, NotSerialized)
            {
                Name(NFBU, Buffer(0x4)
                {
	0x00
                })
                CreateField(NFBU, Zero, 0x4, DAVF)
                CreateField(NFBU, 0x4, One, LIDF)
                CreateField(NFBU, 0x8, 0x6, DTOG)
                CreateField(NFBU, 0x14, One, LIDS)
                If((DerefOf(Arg0[0x3])) & One)
                {
                    Local0 = (DerefOf(Arg0[One]))
                    Local0 = Local0 >> 0x4
                    Local1 = (DerefOf(Arg0[0x2]))
                    Local1 = Local1 << 0x4
                    Local0 = Local0 | Local1
                    CTOI = ^GATD(Local0)
                    Local0 = CTOI + One
                    If(Local0 > ^TTIN())
                    {
                        Local0 = One
                    }
                    DTOG = Local0
                }
                Else
                {
                    If((DerefOf(Arg0[0x3])) & 0x80)
                    {
                        Local0 = (DerefOf(Arg0[0x3]))
                        Local0 = Local0 & 0x3e
                        Local0 = Local0 >> One
                        CTOI = Local0
                        DTOG = CTOI
                    }
                    Else
                    {
                        DTOG = CTOI
                        If(CondRefOf(^LIDB, Local7))
                        {
                            LIDS = \_SB_.GFXC.LIDB
                        }
                    }
                }
                Return(NFBU)
            }
            Method(TTIN, 0x0, NotSerialized)
            {
                Local0 = GDOD(\_SB_.GFXC._DOD)
                Local1 = (SizeOf(Local0))
                Local0 = Zero
                While(Local1)
                {
                    Local0 = Local1 + Local0
                    Local1--
                }
                Return(Local0)
            }
            Method(GATD, 0x1, NotSerialized)
            {
                Local0 = GDOD(\_SB_.GFXC._DOD)
                Local1 = (SizeOf(Local0))
                Local2 = One
                Local3 = One
                While(Local1)
                {
                    Local1--
                    If(Arg0 == Local3)
                    {
                        Return(Local2)
                    }
                    Local3 = Local3 << One
                    Local2++
                }
                Local1 = (SizeOf(Local0))
                Local3 = 0x2
                Local4 = One
                Local1--
                While(Local1)
                {
                    Local5 = Local1
                    Local6 = Local3
                    While(Local5)
                    {
                        If(Arg0 == (Local4 | Local6))
                        {
                            Return(Local2)
                        }
                        Local6 = Local6 << One
                        Local2++
                        Local5--
                    }
                    Local3 = Local3 << One
                    Local4 = Local4 << One
                    Local1--
                }
                Return(One)
            }
        }
        Device(SDM1)
        {
            Method(_HID, 0x0, NotSerialized)
            {
                Return("NVDA0112")
            }
            Name(_CID, "PNP0D40")
            Name(_UID, Zero)
            Method(_CRS, 0x0, NotSerialized)
            {
                Local0 = GCRS(0x78000000, 0x200, 0x2e)
                If(CondRefOf(^CRSA, Local7))
                {
                    ConcatenateResTemplate(Local0, ^CRSA, Local1)
                    Local0 = Local1
                }
                Return(Local0)
            }
            Name(STAF, Zero)
            Method(_STA, 0x0, NotSerialized)
            {
                If(^STAF)
                {
                    Return(0xf)
                }
                If(!^^SD1E)
                {
                    ^STAF = One
                    Return(0xf)
                }
                Return(Zero)
            }
            Method(_DEP, 0x0, NotSerialized)
            {
                If(CondRefOf(^CRSA, Local7))
                {
                    If(CondRefOf(\_SB_.PMUD, Local6))
                    {
                        Return(Package(0x2)
                        {
                            \_SB_.PEPD,
                            \_SB_.PMUD
                        })
                    }
                }
                Return(Package(0x1)
                {
                    \_SB_.PEPD
                })
            }
        }
        Device(SDM2)
        {
            Method(_HID, 0x0, NotSerialized)
            {
                Return("NVDA0112")
            }
            Name(_CID, "PNP0D40")
            Name(_UID, One)
            Method(_CRS, 0x0, NotSerialized)
            {
                Local0 = GCRS(0x78000200, 0x200, 0x2f)
                If(CondRefOf(^CRSA, Local7))
                {
                    ConcatenateResTemplate(Local0, ^CRSA, Local1)
                    Local0 = Local1
                }
                Return(Local0)
            }
            Name(STAF, Zero)
            Method(_STA, 0x0, NotSerialized)
            {
                If(^STAF)
                {
                    Return(0xf)
                }
                If(!^^SD2E)
                {
                    ^STAF = One
                    Return(0xf)
                }
                Return(Zero)
            }
            Method(_DEP, 0x0, NotSerialized)
            {
                If(CondRefOf(\_SB_.PMUD, Local6))
                {
                    Return(Package(0x2)
                    {
                        \_SB_.PEPD,
                        \_SB_.PMUD
                    })
                }
                Return(Package(0x1)
                {
                    \_SB_.PEPD
                })
            }
        }
        Device(SDM3)
        {
            Method(_HID, 0x0, NotSerialized)
            {
                Return("NVDA0112")
            }
            Name(_CID, "PNP0D40")
            Name(_UID, 0x2)
            Method(_CRS, 0x0, NotSerialized)
            {
                Local0 = GCRS(0x78000400, 0x200, 0x33)
                If(CondRefOf(^CRSA, Local7))
                {
                    ConcatenateResTemplate(Local0, ^CRSA, Local1)
                    Local0 = Local1
                }
                Return(Local0)
            }
            Name(STAF, Zero)
            Method(_STA, 0x0, NotSerialized)
            {
                If(^STAF)
                {
                    Return(0xf)
                }
                If(!^^SD3E)
                {
                    ^STAF = One
                    Return(0xf)
                }
                Return(Zero)
            }
            Method(_DEP, 0x0, NotSerialized)
            {
                Return(Package(0x1)
                {
                    \_SB_.PEPD
                })
            }
        }
        Device(SDM4)
        {
            Method(_HID, 0x0, NotSerialized)
            {
                Return("NVDA0112")
            }
            Name(_CID, "PNP0D40")
            Name(_UID, 0x3)
            Method(_CRS, 0x0, NotSerialized)
            {
                Local0 = GCRS(0x78000600, 0x200, 0x3f)
                If(CondRefOf(^CRSA, Local7))
                {
                    ConcatenateResTemplate(Local0, ^CRSA, Local1)
                    Local0 = Local1
                }
                Return(Local0)
            }
            Name(STAF, Zero)
            Method(_STA, 0x0, NotSerialized)
            {
                If(^STAF)
                {
                    Return(0xf)
                }
                If(!^^SD4E)
                {
                    ^STAF = One
                    Return(0xf)
                }
                Return(Zero)
            }
            Method(_DIS, 0x0, NotSerialized)
            {
            }
            Name(_DEP, Package(0x1)
            {
                \_SB_.PEPD
            })
        }
        Scope(SDM4)
        {
            Device(STOR)
            {
                Name(_ADR, 0x8)
                Method(_RMV, 0x0, NotSerialized)
                {
                    Return(Zero)
                }
                Method(_DIS, 0x0, NotSerialized)
                {
                }
                Method(_STA, 0x0, NotSerialized)
                {
                    Return(0xf)
                }
                Device(EMMC)
                {
                    Name(_ADR, 0x8)
                }
            }
        }
        Device(AUDI)
        {
            Method(_HID, 0x0, NotSerialized)
            {
                Return("NVDA0107")
            }
            Method(_DIS, 0x0, NotSerialized)
            {
            }
            Method(_CRS, 0x0, NotSerialized)
            {
                Local1 = CRS3(0x70080000, 0x10000, 0x87, One, 0x16)
                ConcatenateResTemplate(Local1, CRSD(0x2, 0x18), Local0)
                If(CondRefOf(^CRSA, Local7))
                {
                    ConcatenateResTemplate(Local0, ^CRSA, Local1)
                    Local0 = Local1
                }
                Return(Local0)
            }
            Name(STAF, Zero)
            Method(_STA, 0x0, NotSerialized)
            {
                If(^STAF)
                {
                    Return(0xf)
                }
                If(!^^I2SE)
                {
                    ^STAF = One
                    Return(0xf)
                }
                Return(Zero)
            }
        }
        Device(HDAU)
        {
            Method(_HID, 0x0, NotSerialized)
            {
                Return("NVDA010F")
            }
            Name(_CLS, 0x4000300000000)
            Method(_DIS, 0x0, NotSerialized)
            {
            }
            OperationRegion(HDAR, SystemMemory, 0x70030000, 0x200)
            Field(HDAR, DWordAcc, NoLock, Preserve)
            {
                BA0L, 20,
                Offset(0x40),
                BA0S, 32,
                Offset(0x180),
                FPCI, 1
            }
            Method(_CRS, 0x0, NotSerialized)
            {
                Local0 = BA0L * 0x1000
                Return(GCRS(^BA0S, Local0, 0x71))
            }
            Name(STAF, Zero)
            Method(_STA, 0x0, NotSerialized)
            {
                If(^STAF)
                {
                    Return(0xf)
                }
                If(!^^HDAE)
                {
                    ^STAF = One
                    Return(0xf)
                }
                Return(Zero)
            }
        }
        Device(GPIO)
        {
            Method(_HID, 0x0, NotSerialized)
            {
                Return("NVDA0008")
            }
            Name(_UID, Zero)
            Method(_CRS, 0x0, NotSerialized)
            {
                Local0 = CRSG(0x6000d000, 0x80, 0x40)
                ConcatenateResTemplate(Local0, CRSG(0x6000d100, 0x80, 0x41), Local1)
                ConcatenateResTemplate(Local1, CRSG(0x6000d200, 0x80, 0x42), Local0)
                ConcatenateResTemplate(Local0, CRSG(0x6000d300, 0x80, 0x43), Local1)
                ConcatenateResTemplate(Local1, CRSG(0x6000d400, 0x80, 0x57), Local0)
                ConcatenateResTemplate(Local0, CRSG(0x6000d500, 0x80, 0x77), Local1)
                ConcatenateResTemplate(Local1, CRSG(0x6000d600, 0x80, 0x79), Local0)
                ConcatenateResTemplate(Local0, CRSG(0x6000d700, 0x80, 0x9d), Local1)
                Return(Local1)
            }
            Name(AVBL, Zero)
            Method(_REG, 0x2, NotSerialized)
            {
                If(Arg0 == 0x8)
                {
                    AVBL = Arg1
                }
            }
            Method(_DSM, 0x4, NotSerialized)
            {
                If(Arg0 == (Buffer(0x10)
                {
	0x40, 0x8f, 0x24, 0x4f, 0xe2, 0xd5, 0x9f, 0x49, 0x83, 0x4c, 0x27, 0x75,
	0x8e, 0xa1, 0xcd, 0x3f
                }))
                {
                    If(Arg2 == Zero)
                    {
                        If(Arg1 == Zero)
                        {
                            If(CondRefOf(^GPK_, Local6))
                            {
                                Return(Buffer(One)
                                {
	0x03
                                })
                            }
                            Else
                            {
                                Return(Buffer(One)
                                {
	0x01
                                })
                            }
                        }
                    }
                    If(Arg2 == One)
                    {
                        Return(^GPK_)
                    }
                }
                Return(Buffer(One)
                {
	0x00
                })
            }
        }
        Device(SATA)
        {
            Method(_HID, 0x0, NotSerialized)
            {
                Return("NVDA0104")
            }
            OperationRegion(SATR, SystemMemory, 0x70020000, 0x10000)
            Field(SATR, DWordAcc, NoLock, Preserve)
            {
                Offset(0x14),
                SATL, 32,
                Offset(0x54),
                SATS, 32
            }
            Method(_CRS, 0x0, NotSerialized)
            {
                Local0 = SATL * 0x1000
                Return(GCRS(^SATS, Local0, 0x37))
            }
            Method(_STA, 0x0, NotSerialized)
            {
                If(^SATL == 0xffffffff)
                {
                    Return(Zero)
                }
                Else
                {
                    If(^SATL == Zero)
                    {
                        Return(Zero)
                    }
                    Else
                    {
                        Return(0xff)
                    }
                }
            }
        }
        Device(PMSD)
        {
            Method(_HID, 0x0, NotSerialized)
            {
                Return("NVDA0106")
            }
            Method(_STA, 0x0, NotSerialized)
            {
                If(CondRefOf(^CRSA, Local7))
                {
                    Return(0xf)
                }
                Else
                {
                    Return(Zero)
                }
            }
            Method(_CRS, 0x0, NotSerialized)
            {
                If(CondRefOf(^CRSA, Local7))
                {
                    Return(^CRSA)
                }
            }
        }
        Device(DWMI)
        {
            Name(_HID, 0x140cd041)
            Name(_UID, Zero)
            Name(_WDG, Buffer(0x14)
            {
	0x80, 0xe0, 0x7f, 0x99, 0x66, 0xd4, 0x2a, 0x43, 0xa7, 0xbb, 0x24, 0xc6,
	0x93, 0x2c, 0x83, 0x60, 0x30, 0x30, 0x01, 0x01
            })
            Method(WQ00, 0x0, NotSerialized)
            {
                Return(\_SB_.BPBT)
            }
        }
    }
}
