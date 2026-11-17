`default_nettype none
module va_parser(input wire clk,rst_n,busy,valid,input wire [7:0] data,
 output reg launch,output reg [7:0] mx,mz,my, output reg [15:0] seed,output reg [5:0] flags);
 reg [79:0] keyword;
 reg [3:0] keylen;
 reg [2:0] token;
 reg digits,bad,discard,finished;
 reg [15:0] accum;
 reg [7:0] dx,dz,dy;
 reg [15:0] ds;
 wire [19:0] next_decimal={4'b0,accum}*4'd10+{16'b0,data[3:0]};
 task save_number;
 begin
  case(token)
   1:dx<=accum==0?8'd1:accum[7:0];
   2:dz<=accum==0?8'd1:accum[7:0];
   3:dy<=accum==0?8'd1:accum[7:0];
   4:ds<=accum;
   default:begin end
  endcase
 end endtask
 always @(posedge clk) begin
  if(!rst_n) begin keyword<=0;keylen<=0;token<=0;digits<=0;bad<=0;discard<=0;finished<=0;accum<=0;
   launch<=0;mx<=12;mz<=12;my<=8;seed<=1;flags<=0;dx<=1;dz<=1;dy<=1;ds<=1;end
  else begin
   launch<=0;
   if(valid) begin
    if(data==10) begin
     if(!busy&&!discard&&!bad) begin
      if(token==5&&digits) begin mx<=dx;mz<=dz;my<=dy;seed<=ds;flags<=accum[5:0];launch<=1;end
      if(token==0&&keyword=="TEST_CASA") begin mx<=12;mz<=12;my<=8;seed<=1;flags<=0;launch<=1;end
      if(token==0&&keyword=="TEST_SPAWN") begin mx<=30;mz<=30;my<=12;seed<=1;flags<=1;launch<=1;end
     end
     keyword<=0;keylen<=0;token<=0;digits<=0;bad<=0;discard<=0;finished<=0;accum<=0;
    end else if(busy) discard<=1;
    else if(data==13) begin end
    else if(!discard) begin
     if(data==32) begin
      if(token==0&&keylen!=0) begin
       if(keyword=="BUILD") token<=1;
       else if(keyword!="TEST_CASA"&&keyword!="TEST_SPAWN") bad<=1;
      end else if(digits) begin
       if(token<5) begin save_number;token<=token+1'b1;accum<=0;digits<=0;end
       else finished<=1;
      end
     end else if(token==0) begin
      if(keylen==10) bad<=1;else begin keyword<={keyword[71:0],data};keylen<=keylen+1'b1;end
     end else if(data>=48&&data<=57) begin
      if(finished) bad<=1;
      digits<=1;
      if(token<=3&&next_decimal>255) accum<=255;else accum<=next_decimal[15:0];
     end else bad<=1;
    end
   end
  end
 end
endmodule
