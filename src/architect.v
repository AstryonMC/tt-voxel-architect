`default_nettype none
module tt_um_astryon_voxel_architect #(
 parameter CLK_HZ=66000000, BAUD=115200
)(input wire [7:0] ui_in, output wire [7:0] uo_out,
 input wire [7:0] uio_in,output wire [7:0] uio_out,uio_oe,
 input wire ena,clk,rst_n);
 wire [7:0] rxdata;wire rxvalid,rxactive,txready,txactive,tx;
 reg busy,done;
 wire launch;wire [7:0] mx,mz,my;wire [15:0] seed;wire [5:0] flags;
 va_uart_rx #(.CLK_HZ(CLK_HZ),.BAUD(BAUD)) rxunit(clk,rst_n,ui_in[3],rxdata,rxvalid,rxactive);
 va_parser parser(clk,rst_n,busy,rxvalid,rxdata,launch,mx,mz,my,seed,flags);
 reg txvalid;reg [7:0] txdata;
 va_uart_tx #(.CLK_HZ(CLK_HZ),.BAUD(BAUD)) txunit(clk,rst_n,txvalid,txdata,txready,tx,txactive);
 assign uio_out=0;assign uio_oe=0;
 reg [2:0] archetype;
 assign uo_out={archetype,tx,rxactive,txactive,done,busy};
 wire unused=&{ena,uio_in,ui_in[4],1'b0};
 reg startmeta,startsync,startlast;
 reg [15:0] counter,rng;
 reg [1:0] palette;
 reg [7:0] xmax,ymax,zmax;
 reg [9:0] pc;
 reg [2:0] axis;
 reg [7:0] bounds[0:5];
 reg [9:0] expr;
 reg signed [12:0] value;
 reg [6:0] block;
 reg [5:0] state;
 reg single;
 reg [5:0] pos;
 reg [2:0] coord;
 reg [7:0] remainder;
 reg [3:0] hundreds,tens;
 reg [1:0] digit;
 reg [7:0] ix,iz,top,bottom;
 reg [1:0] layer;
 reg [2:0] depth;
 wire [7:0] distx=ix>(xmax>>1)?ix-(xmax>>1):(xmax>>1)-ix;
 wire [7:0] distz=iz>(zmax>>1)?iz-(zmax>>1):(zmax>>1)-iz;
 wire [2:0] depthx=({3'b0,distx}<<3)>=({3'b0,xmax}+1'b1)*4?3'd4:
   ({3'b0,distx}<<3)>=({3'b0,xmax}+1'b1)*3?3'd3:
   ({3'b0,distx}<<3)>=({3'b0,xmax}+1'b1)*2?3'd2:
   ({3'b0,distx}<<3)>=({3'b0,xmax}+1'b1)?3'd1:3'd0;
 wire [2:0] depthz=({3'b0,distz}<<3)>=({3'b0,zmax}+1'b1)*4?3'd4:
   ({3'b0,distz}<<3)>=({3'b0,zmax}+1'b1)*3?3'd3:
   ({3'b0,distz}<<3)>=({3'b0,zmax}+1'b1)*2?3'd2:
   ({3'b0,distz}<<3)>=({3'b0,zmax}+1'b1)?3'd1:3'd0;
 wire [3:0] island_depth={1'b0,depthx}+{1'b0,depthz};
 wire [15:0] next_rng={rng[14:0],rng[15]^rng[13]^rng[12]^rng[10]};
 localparam IDLE=0,INIT=1,FETCH=2,EVAL=3,CLIP=4,CHECK=5,PREFIX=6,TILDE=7,
  DEC_INIT=8,DEC_H=9,DEC_T=10,DEC_OUT=11,SPACE=12,NAME=13,NL=14,NEXT=15,
  DONE=16,DRAIN=17,ISLAND=18,ISLAND_HEIGHT=19,ISLAND_BOX=20,ISLAND_NEXT=21;
 `include "rom.vh"
 function [7:0] prefix_char;input is_single;input [5:0] n;
 begin
  if(is_single) case(n)
   0:prefix_char="/";1:prefix_char="s";2:prefix_char="e";3:prefix_char="t";
   4:prefix_char="b";5:prefix_char="l";6:prefix_char="o";7:prefix_char="c";
   8:prefix_char="k";default:prefix_char=" ";endcase
  else case(n)
   0:prefix_char="/";1:prefix_char="f";2:prefix_char="i";3:prefix_char="l";
   4:prefix_char="l";default:prefix_char=" ";endcase
 end endfunction
 always @* begin
  txvalid=0;txdata=0;
  case(state)
   PREFIX:begin txvalid=1;txdata=prefix_char(single,pos);end
   TILDE:begin txvalid=1;txdata="~";end
   DEC_OUT:begin txvalid=1;case(digit) 0:txdata=48+{4'b0,hundreds};1:txdata=48+{4'b0,tens};default:txdata=48+remainder;endcase end
   SPACE:begin txvalid=1;txdata=" ";end
   NAME:begin txdata=name_char(block,pos);txvalid=txdata!=0;end
   NL:begin txvalid=1;txdata=10;end
   DONE:begin txvalid=1;case(pos) 0:txdata="D";1:txdata="O";2:txdata="N";3:txdata="E";default:txdata=10;endcase end
   default:begin end
  endcase
 end
 integer i;
 always @(posedge clk) begin
  if(!rst_n) begin
   startmeta<=0;startsync<=0;startlast<=0;counter<=0;rng<=1;busy<=0;done<=0;
   archetype<=0;palette<=0;xmax<=0;ymax<=0;zmax<=0;pc<=0;axis<=0;expr<=0;value<=0;
   block<=0;state<=IDLE;single<=0;pos<=0;coord<=0;remainder<=0;hundreds<=0;tens<=0;digit<=0;
   ix<=0;iz<=0;top<=0;bottom<=0;layer<=0;depth<=0;
   for(i=0;i<6;i=i+1) bounds[i]<=0;
  end else begin
   counter<=counter+1'b1;startmeta<=ui_in[0];startsync<=startmeta;startlast<=startsync;
   case(state)
    IDLE:if(launch||(startsync&&!startlast)) begin
     busy<=1;done<=0;state<=INIT;
     if(launch) begin
      xmax<=mx-1'b1;ymax<=my-1'b1;zmax<=mz-1'b1;rng<=seed==0?16'd1:seed;
      archetype<=flags[3:0]>4?3'd0:flags[2:0];palette<=flags[5:4];
     end else begin
      archetype<=ui_in[7:5]>4?3'd0:ui_in[7:5];palette<=ui_in[2:1];rng<=counter==0?16'd1:counter;
      case(ui_in[7:5])
       1:begin xmax<=29;zmax<=29;ymax<=11;end
       2:begin xmax<=25;zmax<=25;ymax<=17;end
       3:begin xmax<=17;zmax<=17;ymax<=9;end
       4:begin xmax<=21;zmax<=21;ymax<=9;end
       default:begin xmax<=11;zmax<=11;ymax<=7;end
      endcase
     end
    end
    INIT:begin
     pc<=first_pc(archetype);axis<=0;ix<=0;iz<=0;layer<=0;
     if(xmax<7||ymax<7||zmax<7) begin
      bounds[0]<=0;bounds[1]<=0;bounds[2]<=0;bounds[3]<=xmax;bounds[4]<=0;bounds[5]<=zmax;
      block<=block_id(0,palette,0);state<=CHECK;pc<=last_pc(archetype);
     end else if(archetype==4) state<=ISLAND;
     else state<=FETCH;
    end
    FETCH:if(pc==last_pc(archetype)) begin state<=DONE;pos<=0;end
     else begin expr<=expression(pc,axis);state<=EVAL;end
    EVAL:begin
     case(axis)
      0,3:value<=$signed({1'b0,(({4'b0,xmax}*expr[9:6])>>3)})+$signed({{7{expr[5]}},expr[5:0]});
      1,4:value<=$signed({1'b0,(({4'b0,ymax}*expr[9:6])>>3)})+$signed({{7{expr[5]}},expr[5:0]});
      default:value<=$signed({1'b0,(({4'b0,zmax}*expr[9:6])>>3)})+$signed({{7{expr[5]}},expr[5:0]});
     endcase
     state<=CLIP;
    end
    CLIP:begin
     if(value<0) bounds[axis]<=0;
     else case(axis)
      0,3:bounds[axis]<=value>$signed({5'b0,xmax})?xmax:value[7:0];
      1,4:bounds[axis]<=value>$signed({5'b0,ymax})?ymax:value[7:0];
      default:bounds[axis]<=value>$signed({5'b0,zmax})?zmax:value[7:0];
     endcase
     if(axis==5) begin axis<=0;rng<=next_rng;block<=block_id(role(pc),palette,next_rng[1:0]);state<=CHECK;end
     else begin axis<=axis+1'b1;state<=FETCH;end
    end
    CHECK:begin
     single<=bounds[0]==bounds[3]&&bounds[1]==bounds[4]&&bounds[2]==bounds[5];pos<=0;coord<=0;
     if(bounds[0]>bounds[3]||bounds[1]>bounds[4]||bounds[2]>bounds[5]) state<=NEXT;
     else state<=PREFIX;
    end
    PREFIX:if(txready) begin
     if((single&&pos==9)||(!single&&pos==5)) begin state<=TILDE;pos<=0;end else pos<=pos+1'b1;
    end
    TILDE:if(txready) state<=DEC_INIT;
    DEC_INIT:begin remainder<=bounds[coord];hundreds<=0;tens<=0;state<=DEC_H;end
    DEC_H:if(remainder>=100) begin remainder<=remainder-100;hundreds<=hundreds+1'b1;end else state<=DEC_T;
    DEC_T:if(remainder>=10) begin remainder<=remainder-10;tens<=tens+1'b1;end
     else begin digit<=hundreds!=0?0:tens!=0?1:2;state<=DEC_OUT;end
    DEC_OUT:if(txready) begin if(digit==2) state<=SPACE;else digit<=digit+1'b1;end
    SPACE:if(txready) begin
     if((single&&coord==2)||coord==5) begin state<=NAME;pos<=0;end
     else begin coord<=coord+1'b1;state<=TILDE;end
    end
    NAME:if(name_char(block,pos)==0) state<=NL;else if(txready) pos<=pos+1'b1;
    NL:if(txready) state<=NEXT;
    NEXT:begin
     if(archetype==4&&xmax>=7&&ymax>=7&&zmax>=7&&iz<=zmax) state<=ISLAND_NEXT;
     else if(pc>=last_pc(archetype)) begin state<=DONE;pos<=0;end
     else begin pc<=pc+1'b1;state<=FETCH;end
    end
    DONE:if(txready) begin if(pos==4) state<=DRAIN;else pos<=pos+1'b1;end
    DRAIN:if(txready) begin busy<=0;done<=1;state<=IDLE;end
    ISLAND:begin
     if(island_depth>=4) begin layer<=2;state<=ISLAND_NEXT;end
     else begin
      depth<=island_depth[2:0];
      rng<=next_rng;top<=(ymax>>1)+{7'b0,next_rng[0]};state<=ISLAND_HEIGHT;layer<=0;
     end
    end
    ISLAND_HEIGHT:begin bottom<={5'b0,depth}>top?top:{5'b0,depth};state<=ISLAND_BOX;end
    ISLAND_BOX:begin
     bounds[0]<=ix;bounds[3]<=ix;bounds[2]<=iz;bounds[5]<=iz;bounds[4]<=top;
     if(layer==0) begin bounds[1]<=bottom;block<=block_id(6'd20,palette,0);end
     else if(layer==1) begin bounds[1]<=top>bottom?top-1'b1:bottom;block<=block_id(6'd19,palette,0);end
     else begin bounds[1]<=top;block<=block_id(6'd18,palette,0);end
     state<=CHECK;
    end
    ISLAND_NEXT:begin
     if(layer!=2) begin layer<=layer+1'b1;state<=ISLAND_BOX;end
     else begin layer<=0;
      if(iz==zmax) begin
       if(ix==xmax) begin iz<=zmax+1'b1;state<=FETCH;end
       else begin ix<=ix+1'b1;iz<=0;state<=ISLAND;end
      end else begin iz<=iz+1'b1;state<=ISLAND;end
     end
    end
    default:state<=IDLE;
   endcase
  end
 end
endmodule
