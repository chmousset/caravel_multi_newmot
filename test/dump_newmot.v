`timescale 1ns/1ns
module dump();
    initial begin
        $dumpfile ("newmot.vcd");
        $dumpvars (0, top);
        #1;
    end
endmodule
