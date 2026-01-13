module top (
    // UART interface
    input  logic ble_uart_rx,
    input  logic CLOCK_100,
    output logic ble_uart_tx,

    // LEDs
    output logic [15:0] LD,

    // Buttons
    input  logic [3:0] BTN,

    // Switches
    input  logic [15:0] SW,

    // Anodes and segments
    output logic [3:0] D1_AN, D2_AN,
    output logic [7:0] D1_SEG, D2_SEG

);

  logic [7:0] rx_data;
  logic en;

  // Instantiate UART module
  uart #(
    .BAUD_RATE   (115_200),
    .CLOCK_FREQ  (100_000_000),
    .DATA_BITS   (8)
  ) uart_inst (
    .clock      (CLOCK_100),
    .reset      (BTN[0]),
    .tx_data    (SW[7:0]),          // Example data to send
    .tx_send    (BTN[1]),         // Send data on button press
    .tx_busy    (),                // Unused in this example
    .rx_data    (rx_data),
    .rx_valid   (en),
    .rx         (ble_uart_tx),  // loopback
    .tx         (ble_uart_tx)
  );

  // Instantiate SSegDriver
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
  assign HEX7 = received_val;
  assign HEX6 = rx_data;
  assign HEX0 = SW[7:0];

  // Register
  always_ff @(posedge CLOCK_100 or posedge BTN[0]) begin
      if (BTN[0]) begin
        received_val <= '0;
      end else if (en) begin
        received_val <= rx_data;
      end
  end

endmodule: top
