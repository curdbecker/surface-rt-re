// CreatorID=INTL	CreatorRev=20.11.790
// FileLength=770	FileChkSum=0xab

DefinitionBlock("SSDT0001.bin", "SSDT", 0x02, "MSFT  ", "fTPM    ", 0x00000002)
{
    Scope(\_SB_)
    {
        Device(TPM2)
        {
            Name(_ADR, Zero)
            Name(_HID, "MSFT0101")
            Name(_CID, "MSFT0101")
            Name(_UID, One)
            Name(_DDN, "Microsoft TPM 2.0")
            Name(_STR, Buffer(0x24)
            {
	0x4d, 0x00, 0x69, 0x00, 0x63, 0x00, 0x72, 0x00, 0x6f, 0x00, 0x73, 0x00,
	0x6f, 0x00, 0x66, 0x00, 0x74, 0x00, 0x20, 0x00, 0x54, 0x00, 0x50, 0x00,
	0x4d, 0x00, 0x20, 0x00, 0x32, 0x00, 0x2e, 0x00, 0x30, 0x00, 0x00, 0x00
            })
            Method(_CRS, 0x0, NotSerialized)
            {
                Name(RBUF, Buffer(0x2)
                {
	0x79, 0x00
                })
                Return(RBUF)
            }
            Method(_STA, 0x0, NotSerialized)
            {
                Return(0xf)
            }
            Method(MORS, 0x3, Serialized)
            {
                Name(_T_0, Zero)
                If(!(Arg0 == One))
                {
                    Return(One)
                }
                While(One)
                {
                    _T_0 = (ToInteger(Arg1, ))
                    If(_T_0 == Zero)
                    {
                        Return(Buffer(One)
                        {
	0x01
                        })
                    }
                    Else
                    {
                        If(_T_0 == One)
                        {
                            Return(Zero)
                        }
                    }
                    Break
                }
                Return(One)
            }
            Method(_DSM, 0x4, Serialized)
            {
                Name(_T_0, Zero)
                If(Arg0 == (Buffer(0x10)
                {
	0xed, 0x54, 0x60, 0x37, 0x13, 0xcc, 0x75, 0x46, 0x90, 0x1c, 0x47, 0x56,
	0xd7, 0xf2, 0xd4, 0x5d
                }))
                {
                    Return(MORS(Arg1, Arg2, Arg3))
                }
                If(!(Arg0 == (Buffer(0x10)
                {
	0xa6, 0xfa, 0xdd, 0x3d, 0x1b, 0x36, 0xb4, 0x4e, 0xa4, 0x24, 0x8d, 0x10,
	0x08, 0x9d, 0x16, 0x53
                })))
                {
                    Return(Zero)
                }
                If(!(Arg1 == One))
                {
                    Return(Zero)
                }
                While(One)
                {
                    _T_0 = (ToInteger(Arg2, ))
                    If(_T_0 == Zero)
                    {
                        Return(Buffer(0x2)
                        {
	0xff, 0x01
                        })
                    }
                    Else
                    {
                        If(_T_0 == One)
                        {
                            Return(PPI1(Arg3))
                        }
                        Else
                        {
                            If(_T_0 == 0x2)
                            {
                                Return(PPI2(Arg3))
                            }
                            Else
                            {
                                If(_T_0 == 0x3)
                                {
                                    Return(PPI3(Arg3))
                                }
                                Else
                                {
                                    If(_T_0 == 0x4)
                                    {
                                        Return(PPI4(Arg3))
                                    }
                                    Else
                                    {
                                        If(_T_0 == 0x5)
                                        {
                                            Return(PPI5(Arg3))
                                        }
                                        Else
                                        {
                                            If(_T_0 == 0x6)
                                            {
                                                Return(PPI6(Arg3))
                                            }
                                            Else
                                            {
                                                If(_T_0 == 0x7)
                                                {
                                                    Return(PPI7(Arg3))
                                                }
                                                Else
                                                {
                                                    If(_T_0 == 0x8)
                                                    {
                                                        Return(PPI8(Arg3))
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                    Break
                }
                Return(Zero)
            }
            Name(NOPC, One)
            Name(NOPM, Zero)
            Name(NOPP, Zero)
            Method(PPI1, 0x1, Serialized)
            {
                Return("1.2")
            }
            Method(PPI2, 0x1, Serialized)
            {
                Return(0x2)
            }
            Method(PPI3, 0x1, Serialized)
            {
                Name(RPAC, Package(0x2)
                {
                    Zero,
                    Zero
                })
                RPAC[One] = \_SB_.PPIP
                Return(RPAC)
            }
            Method(PPI4, 0x1, Serialized)
            {
                Return(Package(0x1)
                {
                    0x2
                })
            }
            Method(PPI5, 0x1, Serialized)
            {
                Name(RPAC, Package(0x3)
                {
                    Zero,
                    Zero,
                    Zero
                })
                RPAC[One] = \_SB_.PPIL
                RPAC[0x2] = \_SB_.PPIR
                Return(RPAC)
            }
            Method(PPI6, 0x1, Serialized)
            {
                Return(0x3)
            }
            Method(PPI7, 0x1, Serialized)
            {
                Local0 = Zero
                \_SB_.PPIP = (DerefOf(Arg0[Zero]))
                Return(Local0)
            }
            Method(PPI8, 0x1, Serialized)
            {
                Name(_T_0, Zero)
                Local0 = 0x4
                Local1 = (DerefOf(Arg0[Zero]))
                While(One)
                {
                    _T_0 = (ToInteger(Local1, ))
                    If(!((Match(Package(0x6)
                    {
                        0xc,
                        0xd,
                        0x11,
                        0x12,
                        0x13,
                        0x14
                    }, MEQ, _T_0, MTR, Zero, Zero)) == Ones))
                    {
                        Local0 = Zero
                    }
                    Break
                }
                Return(Local0)
            }
        }
    }
}
