/*
 * SPDX-FileCopyrightText: 2020 Efabless Corporation
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 * SPDX-License-Identifier: Apache-2.0
 */

#include "verilog/dv/caravel/defs.h"
#include "generated/csr.h"

/*
	IO Test:
		- Configures MPRJ lower 8-IO pins as outputs
		- Observes counter value through the MPRJ lower 8 IO pins (in the testbench)
*/

void main()
{
	/* 
	IO Control Registers
	| DM     | VTRIP | SLOW  | AN_POL | AN_SEL | AN_EN | MOD_SEL | INP_DIS | HOLDH | OEB_N | MGMT_EN |
	| 3-bits | 1-bit | 1-bit | 1-bit  | 1-bit  | 1-bit | 1-bit   | 1-bit   | 1-bit | 1-bit | 1-bit   |

	Output: 0000_0110_0000_1110  (0x1808) = GPIO_MODE_USER_STD_OUTPUT
	| DM     | VTRIP | SLOW  | AN_POL | AN_SEL | AN_EN | MOD_SEL | INP_DIS | HOLDH | OEB_N | MGMT_EN |
	| 110    | 0     | 0     | 0      | 0      | 0     | 0       | 1       | 0     | 0     | 0       |
	
	 
	Input: 0000_0001_0000_1111 (0x0402) = GPIO_MODE_USER_STD_INPUT_NOPULL
	| DM     | VTRIP | SLOW  | AN_POL | AN_SEL | AN_EN | MOD_SEL | INP_DIS | HOLDH | OEB_N | MGMT_EN |
	| 001    | 0     | 0     | 0      | 0      | 0     | 0       | 0       | 0     | 1     | 0       |

	*/

    // 1 input for input signal
	reg_mprj_io_8 =   GPIO_MODE_USER_STD_INPUT_NOPULL;

    // 1 output for segments, starting at 9
	reg_mprj_io_9 =   GPIO_MODE_USER_STD_OUTPUT;

    /* Apply configuration */
    reg_mprj_xfer = 1;
    while (reg_mprj_xfer == 1);

    // activate the project by setting the 1st bit of 2nd bank of LA - depends on the project ID
    reg_la1_iena = 0; // input enable off
    reg_la1_oenb = 0; // output enable on
    reg_la1_data = 1 << 1;

    // PWM test: configure to generate a square wave
    pwm_period_write(400);
    pwm_width_write(200);
    pwm_enable_write(1);

    // Stepper IO setup
    axis_x_stepper_x_mode_write(0b01); // step/dir
    axis_x_stepper_x_invert_step_write(0);
    axis_x_stepper_x_invert_dir_write(0);

    // Stepgen test: generate 10 step forward
    while(!generator_ready_axis_x_ready_read()); // wait for the axis to be ready taking new command
    generator_axis_x_target_position_write(10);
    generator_axis_x_start_speed_write(0);
    generator_axis_x_acceleration_write(100);
    generator_push_motion_write(1);

    // Stepgen test: generate 10 step backwards
    while(!generator_ready_axis_x_ready_read()); // wait for the axis to be ready taking new command
    generator_axis_x_target_position_write(0);
    generator_axis_x_start_speed_write(0);
    generator_axis_x_acceleration_write(-100);
    generator_push_motion_write(1);
    while(!generator_home_done_axis_x_home_done_read()); // wait for all motion completion
}
