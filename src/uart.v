`default_nettype none
module va_uart_rx #(parameter CLK_HZ=66000000, BAUD=115200)(
 input wire clk,rst_n,rx, output reg [7:0] data, output reg valid, output wire active);
 localparam DIV=CLK_HZ/BAUD;
 localparam CW=$clog2(DIV+1);
 reg meta,sync;
 reg [CW-1:0] count;
 reg [3:0] bitno;
 reg [7:0] shift;
 reg [1:0] state;
 assign active=state!=0;
 always @(posedge clk) begin
  if(!rst_n) begin meta<=1;sync<=1;count<=0;bitno<=0;shift<=0;state<=0;data<=0;valid<=0; end
  else begin
   meta<=rx;sync<=meta;valid<=0;
   case(state)
    0: if(!sync) begin count<=DIV/2-1;state<=1;end
    1: if(count!=0) count<=count-1'b1; else if(!sync) begin count<=DIV-1;bitno<=0;state<=2;end else state<=0;
    2: if(count!=0) count<=count-1'b1; else begin
       shift[bitno[2:0]]<=sync;count<=DIV-1;
       if(bitno==7) state<=3; else bitno<=bitno+1'b1;
       end
    3: if(count!=0) count<=count-1'b1; else begin
       state<=0;if(sync) begin data<=shift;valid<=1;end
       end
   endcase
  end
 end
endmodule

module va_uart_tx #(parameter CLK_HZ=66000000, BAUD=115200)(
 input wire clk,rst_n,valid,input wire [7:0] data,output wire ready,output wire tx,output wire active);
 localparam DIV=CLK_HZ/BAUD;
 localparam CW=$clog2(DIV+1);
 reg [CW-1:0] count;
 reg [3:0] remaining;
 reg [9:0] shift;
 assign ready=remaining==0;
 assign active=!ready;
 assign tx=shift[0];
 always @(posedge clk) begin
  if(!rst_n) begin count<=0;remaining<=0;shift<=10'h3ff;end
  else if(ready) begin
   if(valid) begin shift<={1'b1,data,1'b0};remaining<=10;count<=DIV-1;end
  end else if(count!=0) count<=count-1'b1;
  else begin shift<={1'b1,shift[9:1]};remaining<=remaining-1'b1;count<=DIV-1;end
 end
endmodule
