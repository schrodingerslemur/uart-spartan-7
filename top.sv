module top (
  input  logic CLOCK_100,

  // UART signals
  input  logic UART_rxd,
  output logic UART_txd,

  // Buttons and switches
  input  logic [3:0] BTN,
  input  logic [15:0] SW,

  // Anodes and segments
  output logic [3:0] D1_AN, D2_AN,
  output logic [7:0] D1_SEG, D2_SEG
);

  logic en;
  logic [7:0] rx_data;

  uart #(
    .BAUD_RATE   (115_200),
    .CLOCK_FREQ  (100_000_000),
    .DATA_BITS   (8)
  ) uart_inst (
    .clock (CLOCK_100),
    .reset (BTN[0]),

    .tx_data (SW[7:0]),
    .tx_send (BTN[1]),
    .tx_busy (),

    .rx_data (rx_data),
    .rx_valid (en),

    .rx (UART_rxd),
    .tx (UART_txd)
  );

  logic [3:0] HEX0, HEX1, HEX2, HEX3, HEX4,
              HEX5, HEX6, HEX7;
  logic [7:0] received_val;
  EightSevenSegmentDisplays sseg (
    .CLOCK_100,
    .reset(),
    .dec_points(8'b0),
    .blank(8'b0),
    .*
  );

  // Display values
  assign HEX0 = SW[7:0]; // tx value
  assign HEX7 = received_val; // rx value

  // Register
  always_ff @(posedge CLOCK_100 or posedge BTN[0]) begin
      if (BTN[0]) begin
        received_val <= '0;
      end else if (en) begin
        received_val <= rx_data;
      end
  end

endmodule: top