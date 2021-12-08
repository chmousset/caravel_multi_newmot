`default_nettype none
`ifdef FORMAL
    `define MPRJ_IO_PADS 38    
`endif
// update this to the name of your module
module wrapped_newmot(
`ifdef USE_POWER_PINS
    inout vccd1,                    // User area 1 1.8V supply
    inout vssd1,                    // User area 1 digital ground
`endif
    // wishbone interface
    input wire wb_clk_i,            // clock, runs at system clock
    input wire wb_rst_i,            // main system reset
    input wire wbs_stb_i,           // wishbone write strobe
    input wire wbs_cyc_i,           // wishbone cycle
    input wire wbs_we_i,            // wishbone write enable
    input wire [3:0] wbs_sel_i,     // wishbone write word select
    input wire [31:0] wbs_dat_i,    // wishbone data in
    input wire [31:0] wbs_adr_i,    // wishbone address
    output wire wbs_ack_o,          // wishbone ack
    output wire [31:0] wbs_dat_o,   // wishbone data out

    // Logic Analyzer Signals
    // only provide first 32 bits to reduce wiring congestion
    input  wire [31:0] la_data_in,  // from PicoRV32 to your project
    output wire [31:0] la_data_out, // from your project to PicoRV32
    input  wire [31:0] la_oenb,     // output enable bar (low for active)

    // IOs
    input  wire [`MPRJ_IO_PADS-1:0] io_in,  // in to your project
    output wire [`MPRJ_IO_PADS-1:0] io_out, // out fro your project
    output wire [`MPRJ_IO_PADS-1:0] io_oeb, // out enable bar (low active)

    // IRQ
    output wire [2:0] irq,          // interrupt from project to PicoRV32

    // extra user clock
    input wire user_clock2,
    
    // active input, only connect tristated outputs if this is high
    input wire active
);

    // all outputs must be tristated before being passed onto the project
    wire buf_wbs_ack_o;
    wire [31:0] buf_wbs_dat_o;
    wire [31:0] buf_la_data_out;
    wire [`MPRJ_IO_PADS-1:0] buf_io_out;
    wire [`MPRJ_IO_PADS-1:0] buf_io_oeb;
    wire [2:0] buf_irq;

    `ifdef FORMAL
    // formal can't deal with z, so set all outputs to 0 if not active
    assign wbs_ack_o    = active ? buf_wbs_ack_o    : 1'b0;
    assign wbs_dat_o    = active ? buf_wbs_dat_o    : 32'b0;
    assign la_data_out  = active ? buf_la_data_out  : 32'b0;
    assign io_out       = active ? buf_io_out       : {`MPRJ_IO_PADS{1'b0}};
    assign io_oeb       = active ? buf_io_oeb       : {`MPRJ_IO_PADS{1'b0}};
    assign irq          = active ? buf_irq          : 3'b0;
    `include "properties.v"
    `else
    // tristate buffers
    assign wbs_ack_o    = active ? buf_wbs_ack_o    : 1'bz;
    assign wbs_dat_o    = active ? buf_wbs_dat_o    : 32'bz;
    assign la_data_out  = active ? buf_la_data_out  : 32'bz;
    assign io_out       = active ? buf_io_out       : {`MPRJ_IO_PADS{1'bz}};
    assign io_oeb       = active ? buf_io_oeb       : {`MPRJ_IO_PADS{1'bz}};
    assign irq          = active ? buf_irq          : 3'bz;
    `endif

    `define OUTPUT 1'b0
    `define INPUT 1'b1
    `define io_spi_miso 0
    `define io_spi_clk 1
    `define io_spi_cs 2
    `define io_spi_mosi 3
    `define io_pwm_native 4
    `define io_ub_tx 5
    `define io_ub_rx 6
    `define io_gpio_gpio0 7
    `define io_gpio_gpio1 8
    `define io_x_step 9
    `define io_x_dir 10
    `define io_y_step 11
    `define io_y_dir 12
    `define io_pwm 13
    `define io_qei_a 14
    `define io_qei_b 15
    `define io_qei_i 16

    assign buf_io_oeb[`MPRJ_IO_PADS-1: `io_pwm +1] = {(`MPRJ_IO_PADS){`INPUT}};// default all inputs
    assign buf_io_oeb[`io_spi_miso] = `INPUT;
    assign buf_io_oeb[`io_spi_clk] = `OUTPUT;
    assign buf_io_oeb[`io_spi_cs] = `OUTPUT;
    assign buf_io_oeb[`io_spi_mosi] = `OUTPUT;
    assign buf_io_oeb[`io_pwm_native] = `OUTPUT;
    assign buf_io_oeb[`io_ub_tx] = `OUTPUT;
    assign buf_io_oeb[`io_ub_rx] = `INPUT;
    assign buf_io_oeb[`io_x_step] = `OUTPUT;
    assign buf_io_oeb[`io_x_dir] = `OUTPUT;
    assign buf_io_oeb[`io_y_step] = `OUTPUT;
    assign buf_io_oeb[`io_y_dir] = `OUTPUT;
    assign buf_io_oeb[`io_pwm] = `OUTPUT;
    assign buf_io_oeb[`io_qei_a] = `INPUT;
    assign buf_io_oeb[`io_qei_b] = `INPUT;
    assign buf_io_oeb[`io_qei_i] = `INPUT;

    top newmot (

        .sys_clk(wb_clk_i),
        .sys_rst(wb_rst_i),

        // MGMT SoC Wishbone Slave

        .wb_cyc(wbs_cyc_i),
        .wb_stb(wbs_stb_i),
        .wb_we(wbs_we_i),
        .wb_sel(wbs_sel_i),
        .wb_adr(wbs_adr_i[31:2]), // litex does not generate the two lowest significant adress lines
        .wb_dat_r(buf_wbs_dat_o),
        .wb_dat_w(wbs_dat_i),
        .wb_ack(buf_wbs_ack_o),

        // IO Pads
        .pwm(buf_io_out[`io_pwm_native]),
        .stepper0_step(buf_io_out[`io_x_step]),
        .stepper0_dir(buf_io_out[`io_x_dir]),
        .uartbone_tx(buf_io_out[`io_ub_tx]),
        .uartbone_rx(buf_io_out[`io_ub_rx]),
        .pwm_out(buf_io_out[`io_pwm]),
        .qei_a(io_in[`io_qei_a]),
        .qei_b(io_in[`io_qei_b]),
        .qei_i(io_in[`io_qei_i])
    );


endmodule 
`default_nettype wire
