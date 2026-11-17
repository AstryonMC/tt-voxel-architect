import os
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, ValueChange, Timer, with_timeout
from model.architect import stream, DEFAULTS
from tools.render import validate

REAL=os.getenv('REAL')=='yes' or os.getenv('GATES')=='yes'
DIV=66000000//115200 if REAL else 8
PERIOD=15.152 if REAL else 10

async def reset(d):
    d.ena.value=1;d.ui_in.value=8;d.uio_in.value=0;d.rst_n.value=0
    cocotb.start_soon(Clock(d.clk,PERIOD,unit='ns').start())
    await ClockCycles(d.clk,8);d.rst_n.value=1;await ClockCycles(d.clk,8)

async def send(d,line):
    for b in line.encode():
        for bit in [0]+[(b>>i)&1 for i in range(8)]+[1]:
            d.ui_in.value=(int(d.ui_in.value)&~8)|(bit<<3)
            await ClockCycles(d.clk,DIV)

async def receive(d):
    result=bytearray()
    while not result.endswith(b'DONE\n'):
        while int(d.uo_out.value)&16: await ValueChange(d.uo_out)
        await Timer(PERIOD*DIV*1.5,unit='ns')
        b=0
        for i in range(8):
            b|=((int(d.uo_out.value)>>4)&1)<<i
            await Timer(PERIOD*DIV,unit='ns')
        assert int(d.uo_out.value)&16, 'bad stop bit'
        result.append(b)
        await Timer(PERIOD*DIV*.5,unit='ns')
    return result.decode()

async def build(d,line,args):
    rx=cocotb.start_soon(receive(d))
    await send(d,line)
    actual=await with_timeout(rx, max(10000000,len(stream(*args))*DIV*PERIOD*20),'ns')
    d._log.info('Completed %r (%d UART bytes)',line.strip(),len(actual))
    expected=stream(*args)
    assert actual==expected, f'first differing stream: {actual[:200]!r} expected {expected[:200]!r}'
    await ClockCycles(d.clk,DIV*3)
    assert int(d.uo_out.value)&2 and not int(d.uo_out.value)&1
    assert int(d.uio_oe.value)==int(d.uio_out.value)==0
    return actual

@cocotb.test()
async def serial_model_comparison(d):
    await reset(d)
    if REAL:
        await build(d,'BUILD 1 1 1 1 0\n',(1,1,1,1,0))
        return
    for a in range(5):
        for p in range(4):
            dims=DEFAULTS[a] if p==0 else (10+p,12+p,8+p)
            seed=1 if p==0 else 173*p
            args=(*dims,seed,a+16*p)
            text=await build(d,'BUILD '+' '.join(map(str,args))+'\n',args)
            validate(text,dims)
    for args in [(255,9,8,65535,0),(8,255,9,0,19),(13,11,12,65234,4),(300,0,1,65537,63)]:
        await build(d,'BUILD '+' '.join(map(str,args))+'\n',args)
    await build(d,'TEST_CASA\r\n',(12,12,8,1,0))
    await build(d,'TEST_SPAWN\n',(30,30,12,1,1))
    await build(d,'  BUILD   9  10  8  0   48  \r\n',(9,10,8,0,48))
    await build(d,'BUILD 8 12 8 1 0\n',(8,12,8,1,0))
    await build(d,'BUILD 22 22 14 1 4\n',(22,22,14,1,4))
    text=await build(d,'BUILD 255 255 1 1 0\n',(255,255,1,1,0))
    validate(text,(255,255,1),voxelize=False)
    text=await build(d,'BUILD 40 40 40 1 0\n',(40,40,40,1,0))
    validate(text,(40,40,40),voxelize=False)

@cocotb.test(skip=REAL)
async def maximum_build(d):
    await reset(d)
    text=await build(d,'BUILD 255 255 255 1 0\n',(255,255,255,1,0))
    validate(text,(255,255,255),voxelize=False)

@cocotb.test(skip=REAL)
async def parser_and_start(d):
    await reset(d)
    for bad in ['\n','garbage\n','build 1 1 1 1 0\n','BUILD 1 q 1 1 0\n','BUILD 1 1\n']:
        await send(d,bad)
    assert not int(d.uo_out.value)&3
    rx=cocotb.start_soon(receive(d))
    d.ui_in.value=8|(1<<5)|(2<<1)|1
    await ClockCycles(d.clk,10)
    d.ui_in.value=8|(1<<5)|(2<<1)
    await send(d,'TEST_CASA\n')
    actual=await with_timeout(rx,200000000,'ns')
    assert actual==stream(*DEFAULTS[1],1,33) # spawn uses no seeded material
    await ClockCycles(d.clk,DIV*100)
    assert int(d.uo_out.value)&2 and not int(d.uo_out.value)&1
    await build(d,'BUILD 1 1 1 0 15\n',(1,1,1,0,15))
