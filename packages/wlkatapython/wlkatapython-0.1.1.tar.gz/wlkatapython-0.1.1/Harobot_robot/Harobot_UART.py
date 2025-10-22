import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from Mirobot_robot.Mirobot_UART import WLKATA_UART
import serial
import time
import re

#Harobot串口控制类
#Harobot serial port control class


class Harobot_UART(WLKATA_UART):
    #Initialization of robot state dictionary, GPIO enable initialization list, and read/write message flags
    # 初始化机械臂信息字典、GPIO的使能初始化列表、读写消息的标志位

    def __init__(self,block_flag=False,message_flag=False):
        super().__init__(block_flag,message_flag)
        self.Harobot_state_all = {"state": "-1",
                                  "angle_A": -1, "angle_B": -1, "angle_C": -1, "angle_D": -1, "angle_X": -1,
                                  "angle_Y": -1,
                                  "angle_Z": -1,
                                  "coordinate_X": -1, "coordinate_Y": -1, "coordinate_Z": -1, "coordinate_RX": -1,
                                  "coordinate_RY": -1, "coordinate_RZ": -1}
        self.gpio_state = [0, 0, 0, 0]
        

    #Save serial object and robot address (RS458 is (0-255), serial is -1)
    # 保存串口对象及机械臂地址（RS458为（0-255）,串口为-1）

    def init(self, p, adr):
        self.pSerial = p
        self.address = adr
        # self.sendMsg("o175=0")


    #Robot homing
    # 机械臂回零

    def homing(self, mode=8):
        self.restart()
        self.mode = mode
        if self.mode == 0:
            self.sendMsg("o105=0")
        elif self.mode == 1:
            self.sendMsg("o105=1")
        elif self.mode == 2:
            self.sendMsg("o105=2")
        elif self.mode == 3:
            self.sendMsg("o105=3")
        elif self.mode == 4:
            self.sendMsg("o105=4")
        elif self.mode == 5:
            self.sendMsg("o105=5")
        elif self.mode == 6:
            self.sendMsg("o105=6")
        elif self.mode == 7:
            self.sendMsg("o105=7")
        elif self.mode == 8:
            self.sendMsg("o105=8")
        elif self.mode == 9:
            self.sendMsg("o105=9")
        elif self.mode == 10:
            self.sendMsg("o105=10")
        else:
            self.sendMsg("o105=8")
        time.sleep(0.5)
        self.delay_idle()

        # while True:
        #     messages=self.read_message()
        #     if messages == "ok":
        #         return 1
        #     elif messages=="Info,in homing moving...":
        #         time.sleep(0.1)
        #     else:
        #         self.__error_except(self.homing, 1)

    #Execute offline file
    # 执行离线文件-

    def runFile(self, fileName, num=False):
        self.num = num
        if self.num == True:
            self.fileName = "o112" + str(fileName)
            self.sendMsg(self.fileName)
        elif self.num == False:
            self.fileName = "o111" + str(fileName)
            self.sendMsg(self.fileName)
        else:
            self.fileName = "o111" + str(fileName)
            self.sendMsg(self.fileName)

        # self.var_read_message = self.read_message()
        # if self.var_read_message == "ok":
        #     return 1
        # elif self.var_read_message == "error":
        #     self.__error_except(self.runFile, 4)
        # else:
        #     self.__error_except(self.runFile, 1)
        self.delay_idle()        

    #Stop current robot action
    # 停止当前机械臂动作

    # def cancellation(self):
    #     self.sendMsg("o117")
    #     if self.read_message() == "ok":
    #         return 1
    #     else:
    #         self.__error_except(self.cancellation, 1)

    #Gripper control function
    # 夹爪控制函数

    def gripper(self, num):
        self.num = num
        if self.num == 0:
            self.sendMsg("M67 E0 Q0")
        elif self.num == 1:
            self.sendMsg("M67 E0 Q4")
        elif self.num == 2:
            self.sendMsg("M67 E0 Q7.5")
        else:
            self.sendMsg("M67 E0 Q0")
        # if self.read_message() == "ok":
        #     return 1
        # else:
        #     self.__error_except(self.gripper, 1)
        self.delay_idle()

    #Pump control function
    # 气泵控制函数

    def pump(self, num):
        self.num = num
        if self.num == 0:
            self.sendMsg("M67 E0 Q0")
        elif self.num == 1:
            self.sendMsg("M67 E0 Q100")
        elif self.num == 2:
            self.sendMsg("M67 E0 Q50")
        else:
            self.sendMsg("M67 E0 Q0")
        # if self.read_message() == "ok":
        #     return 1
        # else:
        #     self.__error_except(self.pump, 1)
        self.delay_idle()

    #PWM control function, num range 0-100
    # PWM控制函数，num取值范围0-100

    def pwmWrite(self, num):
        self.num = "M67 E0 Q" + str(num)
        self.sendMsg(self.num)
        # if self.read_message() == "ok":
        #     return 1
        # else:
        #     self.__error_except(self.pwmWrite, 1)
        self.delay_idle()

    #Robot returns to zero position in angle mode
    # 机械臂回到角度模式下零点位置

    def zero(self):
        self.sendMsg("G9 G90 X0 Y0 Z0 A0 B0 C0 F4000")
        # if self.read_message() == "ok":
        #     return 1
        # else:
        #     self.__error_except(self.zero, 1)
        self.delay_idle()

    """Robot Cartesian control function,
    motion: 0-fast movement 1-linear movement 2-gantry movement
    position: 0-absolute movement 1-incremental movement
    x/y/z/a/b/c: 6 coordinate values of the robot end
    """
    # 机械臂笛卡尔控制函数，
    # motion：0-快速运动 1-直线运动 
    # position: 0-绝对值运动 1-增量值运动
    # x/y/z/a/b/c: 机械臂末端6个坐标值

    def writecoordinate(self, motion, position, x=None, y=None, z=None, a=None, b=None, c=None):
        self.motion = motion
        self.position = position
        
        if self.motion == 0:
            self.motion = "G07"
        elif self.motion == 1:
            self.motion = "G01"
        else:
            self.motion = "G07"

        if self.position == 0:
            self.position = "G90"
        elif self.position == 1:
            self.position = "G91"
        else:
            self.position = "G90"

        self.coordinate = ""
        if x is not None:
            self.coordinate += f"X{x}"
        if y is not None:
            self.coordinate += f"Y{y}"
        if z is not None:
            self.coordinate += f"Z{z}"
        if a is not None:
            self.coordinate += f"A{a}"
        if b is not None:
            self.coordinate += f"B{b}"
        if c is not None:
            self.coordinate += f"C{c}"

        self.cmd = f"{self.motion}{self.position}{self.coordinate}F4000"
        self.sendMsg(self.cmd)
        # if self.read_message() == "ok":
        #     return 1
        # else:
        #     self.__error_except(self.writecoordinate, 1)
        self.delay_idle()

    #Robot speed control, num:0-100
    # 机械臂速度控制，num:0-100

    def speed(self, num):
        self.num = "F" + str(num)
        self.sendMsg(self.num)
        # if self.read_message() == "ok":
        #     return 1
        # else:
        #     self.__error_except(self.speed, 1)
        self.delay_idle()

    """Robot angle control function
    position: 0-absolute movement 1-incremental movement
     x/y/z/a/b/c/d: angles of 1-7 axes of the robot
    """
    # 机械臂角度控制函数
    # position: 0-绝对值运动 1-增量值运动
    # x/y/z/a/b/c/d: 机械臂1-6轴角度值

    def writeangle(self, position, axle1=None, axle2=None, axle3=None, axle4=None, axle5=None, axle6=None, axle7=None):
        self.position = position
        
        if self.position == 0:
            self.position = "G90"
        elif self.position == 1:
            self.position = "G91"
        else:
            self.position = "G90"

        self.angle = ""
        if axle1 is not None:
            self.angle += f"X{axle1}"
        if axle2 is not None:
            self.angle += f"Y{axle2}"
        if axle3 is not None:
            self.angle += f"Z{axle3}"
        if axle4 is not None:
            self.angle += f"A{axle4}"
        if axle5 is not None:
            self.angle += f"B{axle5}"
        if axle6 is not None:
            self.angle += f"C{axle6}"
        if axle7 is not None:
            self.angle += f"D{axle7}"

        # 组合完整指令
        self.cmd = f"G09{self.position}{self.angle}F4000"
        self.sendMsg(self.cmd)
        # if self.read_message() == "ok":
        #     return 1
        # else:
        #     self.__error_except(self.writeangle, 1)
        self.delay_idle()

    """Robot 7th axis movement
    motion:0-fast movement 1-linear movement
    position: 0-absolute movement 1-incremental movement
    """
    # 机械臂第7轴运动
    # motion:0-快速运动 1-直线运动
    # position: 0-绝对值运动 1-增量值运动

    # def writeexpand(self, motion, position, d):
    #     self.motion = motion
    #     self.position = position
    #     self.coordinate = "D" + str(d)
    #     if self.motion == 0:
    #         self.motion = "G00"
    #     elif self.motion == 1:
    #         self.motion = "G01"
    #     else:
    #         self.motion = "G00"

    #     if self.position == 0:
    #         self.position = "G90"
    #     elif self.position == 1:
    #         self.position = "G91"
    #     else:
    #         self.position = "G90"
    #     self.coordinate = str(self.position) + str(self.motion) + self.coordinate
    #     self.sendMsg(self.coordinate)

        # if self.read_message() == "ok":
        #     return 1
        # else:
        #     self.__error_except(self.writeexpand, 1)

    #Robot restart
    # 机械臂重启

    def restart(self):
        self.sendMsg("o100")
        time.sleep(1)
        # self.delay_idle()
        # if self.read_message() == "ok":
        #     return 1
        # else:
        #     self.__error_except(self.restart, 1)

    #Get robot and multifunction controller firmware version (currently only available through UART, not supported by RS485)
    # 获取机械臂及多功能控制器固件版本（现只能通过UART获得，RS485暂不支持）

    # def version(self):
    #     self.lina = ""
    #     self.lina1 = ""

    #     self.pSerial.flushInput()
    #     self.pSerial.flushOutput()
    #     self.sendMsg("$V")

    #     timeout_cnt = 0

    #     while True:
    #         if timeout_cnt >= 5:
    #             return "Query failed"

    #         self.lina = self.pSerial.readline().decode('utf-8').strip()
    #         self.lina1 = self.pSerial.readline().decode('utf-8').strip()

    #         if self.lina.startswith('EXbox') and self.lina1.startswith(
    #                 'Mirobot'):
    #             break

    #         timeout_cnt += 1
    #         time.sleep(0.1)

    #     return self.lina, self.lina1

    #Error and exception, built-in function
    # 错误和异常，内置函数

    def __error_except(self, f, num):
        if num == 1:
            raise Exception(f"{f.__name__}: No reply - 'ok'")
        elif num == 2:
            raise Exception(f"{f.__name__}: parameter error")
        elif num == 3:
            raise Exception(f"{f.__name__}: regular expression error")
        elif num == 4:
            raise Exception(f"{f.__name__}: File run error")
        else:
            pass

    #Get full status of the robot
    # 获取机械臂全部状态

    def getStatus(self):
        self.line = " "
        self.pSerial.flushInput()
        self.pSerial.flushOutput()
        self.sendMsg("?")
        if self.pSerial.in_waiting > 0:
            self.line = self.read_message()
            if self.line[0] == "<" and self.line[-1] == ">":
                self.data = self.__parse_response(self.line)
            else:
                self.data = -1
        else:
            return "error"

        time.sleep(0.1)
        return self.data


    # 机械臂全部状态的正则表达式

    def __parse_response(self, line):
        self.pattern = r'<(\w+),Cartesian:([-]?\d+\.\d+),([-]?\d+\.\d+),([-]?\d+\.\d+),([-]?\d+\.\d+),([-]?\d+\.\d+),([-]?\d+\.\d+),([-]?\d+\.\d+),Angle:([-]?\d+\.\d+),([-]?\d+\.\d+),([-]?\d+\.\d+),([-]?\d+\.\d+),([-]?\d+\.\d+),([-]?\d+\.\d+),([-]?\d+\.\d+)([|Ov:100,100,100])*>'
        match = re.match(self.pattern, line)
        if match:

            self.Harobot_state_all = {"state": " ",
                                      "angle_A": 0, "angle_B": 0, "angle_C": 0, "angle_D": 0, "angle_X": 0,
                                      "angle_Y": 0, "angle_Z": 0,
                                      "coordinate_X": 0, "coordinate_Y": 0, "coordinate_Z": 0, "coordinate_RX": 0,
                                      "coordinate_RY": 0, "coordinate_RZ": 0}

            self.Harobot_state_all["state"] = match.group(1)
            self.Harobot_state_all["coordinate_X"] = match.group(2)
            self.Harobot_state_all["coordinate_Y"] = match.group(3)
            self.Harobot_state_all["coordinate_Z"] = match.group(4)
            self.Harobot_state_all["coordinate_RX"] = match.group(5)
            self.Harobot_state_all["coordinate_RY"] = match.group(6)
            self.Harobot_state_all["coordinate_RZ"] = match.group(7)
            self.Harobot_state_all["angle_X"] = match.group(9)
            self.Harobot_state_all["angle_Y"] = match.group(10)
            self.Harobot_state_all["angle_Z"] = match.group(11)
            self.Harobot_state_all["angle_A"] = match.group(12)
            self.Harobot_state_all["angle_B"] = match.group(13)
            self.Harobot_state_all["angle_C"] = match.group(14)
            self.Harobot_state_all["angle_D"] = match.group(15)
            return self.Harobot_state_all
        else:
            return "parse error"

    #Get robot state
    # 获取机械臂状态

    def getState(self):
        self.getStatus()
        return self.Harobot_state_all["state"]

    #Get angles of 1-7 axes of the robot
    # 获取机械臂1-7轴角度

    def getAngle(self, num):
        self.num = num
        self.getStatus()
        if num == 1:
            return self.Harobot_state_all["angle_X"]
        elif num == 2:
            return self.Harobot_state_all["angle_Y"]
        elif num == 3:
            return self.Harobot_state_all["angle_Z"]
        elif num == 4:
            return self.Harobot_state_all["angle_A"]
        elif num == 5:
            return self.Harobot_state_all["angle_B"]
        elif num == 6:
            return self.Harobot_state_all["angle_C"]
        elif num == 7:
            return self.Harobot_state_all["angle_D"]
        else:
            self.__error_except(self.getAngle, 2)

    #Get end coordinates of the robot
    # 获取机械臂末端坐标

    def getcoordinate(self, num):
        self.num = num
        self.getStatus()
        if num == 1:
            return self.Harobot_state_all["coordinate_X"]
        elif num == 2:
            return self.Harobot_state_all["coordinate_Y"]
        elif num == 3:
            return self.Harobot_state_all["coordinate_Z"]
        elif num == 4:
            return self.Harobot_state_all["coordinate_RX"]
        elif num == 5:
            return self.Harobot_state_all["coordinate_RY"]
        elif num == 6:
            return self.Harobot_state_all["coordinate_RZ"]
        else:
            self.__error_except(self.getcoordinate, 2)

    #Get end state
    # 获取末端状态

    # def getpump(self):
    #     self.getStatus()
    #     return self.Harobot_state_all["pump"]

    #Get robot motion mode
    # 获取机械臂运动模式

    # def getmooe(self):
    #     self.getStatus()
    #     return self.Harobot_state_all["mooe"]

   

    #GPIO initialization (turn off enable state)
    # gpio初始化（将使能状态关闭）

    # def gpio_init(self):
    #     for i in range(0, 4):
    #         self.gpio_state[i] = 0
    #     self.var_gpio_state = "o132=" + str(self.gpio_state[0]) + "," + str(self.gpio_state[1]) + "," + str(
    #         self.gpio_state[2]) + "," + str(self.gpio_state[3])
    #     self.sendMsg(self.var_gpio_state)
        # if self.read_message() == "ok":
        #     return 1
        # else:
        #     self.__error_except(self.gpio_init, 1)

    #Write GPIO mode
    # gpio模式写入

    # def gpio_mode_write(self, name, num):
    #     self.var_name = name.capitalize()
    #     self.var_num = num
    #     if self.var_name == "A0":
    #         self.var_gpio_state = "o130=" + str(self.var_num) + ",,,"
    #     elif self.var_name == "A1":
    #         self.var_gpio_state = "o130=," + str(self.var_num) + ",,"
    #     elif self.var_name == "D0":
    #         self.var_gpio_state = "o130=,," + str(self.var_num) + ","
    #     elif self.var_name == "D1":
    #         self.var_gpio_state = "o130=,,," + str(self.var_num)
    #     else:
    #         self.__error_except(self.gpio_mode_write, 2)
    #     self.sendMsg(self.var_gpio_state)

        # if self.read_message() == "ok":
        #     return 1
        # else:
        #     self.__error_except(self.gpio_mode_write, 1)

    #Read GPIO mode
    # gpio模式读取

    # def gpio_mode_read(self, name):
    #     self.var_name = name.capitalize()
    #     self.sendMsg("o130?")
    #     self.var_mode_num = self.read_message()
    #     self.var_mode_num1 = self.read_message()
    #     match = re.match('^([\d]+),([\d]+),([\d]+),([\d]+)$', self.var_mode_num)
    #     if match:
    #         if self.var_name == "A0":
    #             return match.group(1)
    #         elif self.var_name == "A1":
    #             return match.group(2)
    #         elif self.var_name == "D0":
    #             return match.group(3)
    #         elif self.var_name == "D1":
    #             return match.group(4)
    #         else:
    #             self.__error_except(self.gpio_mode_read, 2)
    #     else:
    #         self.__error_except(self.gpio_mode_read, 3)

    #Write GPIO digital/analog output
    # gpio数字、模拟输出写入

    # def gpio_output_write(self, name, num):
    #     self.var_name = name.capitalize()
    #     self.var_num = num
    #     if self.var_name == "A0":
    #         self.var_gpio_num = "o131=" + str(self.var_num) + ",,,"
    #     elif self.var_name == "A1":
    #         self.var_gpio_num = "o131=," + str(self.var_num) + ",,"
    #     elif self.var_name == "D0":
    #         self.var_gpio_num = "o131=,," + str(self.var_num) + ","
    #     elif self.var_name == "D1":
    #         self.var_gpio_num = "o131=,,," + str(self.var_num)
    #     else:
    #         self.__error_except(self.gpio_output_write, 2)

    #     self.sendMsg(self.var_gpio_num)
        # if self.read_message() == "ok":
        #     return 1
        # else:
        #     self.__error_except(self.gpio_output_write, 1)

    #Read GPIO input value
    # gpio输入值读取

    # def gpio_input_read(self, name):
    #     self.var_name = name.capitalize()
    #     self.sendMsg("o131?")
    #     self.var_mode_num = self.read_message()
    #     self.var_mode_num1 = self.read_message()
    #     match = re.match('^([\d]+),([\d]+),([\d]+),([\d]+)$', self.var_mode_num)
    #     if match:
    #         if self.var_name == "A0":
    #             return match.group(1)
    #         elif self.var_name == "A1":
    #             return match.group(2)
    #         elif self.var_name == "D0":
    #             return match.group(3)
    #         elif self.var_name == "D1":
    #             return match.group(4)
    #         else:
    #             self.__error_except(self.gpio_input_read, 2)
    #     else:
    #         self.__error_except(self.gpio_input_read, 3)

    #Write GPIO enable
    # gpio使能写入

    # def gpio_enable_write(self, name, num):
    #     self.var_name = name.capitalize()
    #     self.var_num = num
    #     if self.var_name == "A0":
    #         self.var_gpio_num = "o132=" + str(self.var_num) + ",,,"
    #     elif self.var_name == "A1":
    #         self.var_gpio_num = "o132=," + str(self.var_num) + ",,"
    #     elif self.var_name == "D0":
    #         self.var_gpio_num = "o132=,," + str(self.var_num) + ","
    #     elif self.var_name == "D1":
    #         self.var_gpio_num = "o132=,,," + str(self.var_num)
    #     else:
    #         self.__error_except(self.gpio_enable_write, 2)

    #     self.sendMsg(self.var_gpio_num)
        # if self.read_message() == "ok":
        #     return 1
        # else:
        #     self.__error_except(self.gpio_enable_write, 1)

    #Read GPIO enable
    # gpio使能读取

    # def gpio_enable_read(self, name):
    #     self.var_name = name.capitalize()
    #     self.sendMsg("o132?")
    #     self.var_mode_num = self.read_message()
    #     self.var_mode_num1 = self.read_message()
    #     match = re.match('^([\d]+),([\d]+),([\d]+),([\d]+)$', self.var_mode_num)
    #     if match:
    #         if self.var_name == "A0":
    #             return match.group(1)
    #         elif self.var_name == "A1":
    #             return match.group(2)
    #         elif self.var_name == "D0":
    #             return match.group(3)
    #         elif self.var_name == "D1":
    #             return match.group(4)
    #         else:
    #             self.__error_except(self.gpio_enable_read, 2)
    #     else:
    #         self.__error_except(self.gpio_enable_read, 3)

    #Write GPIO pin trigger threshold
    # gpio引脚触发阈值写入

    # def gpio_threshold_write(self, name, num):
    #     self.var_name = name.capitalize()
    #     self.var_num = num
    #     if self.var_name == "A0":
    #         self.var_gpio_num = "o133=" + str(self.var_num) + ",,,"
    #     elif self.var_name == "A1":
    #         self.var_gpio_num = "o133=," + str(self.var_num) + ",,"
    #     elif self.var_name == "D0":
    #         self.var_gpio_num = "o133=,," + str(self.var_num) + ","
    #     elif self.var_name == "D1":
    #         self.var_gpio_num = "o133=,,," + str(self.var_num)
    #     else:
    #         self.__error_except(self.gpio_threshold_write, 2)
    #     self.sendMsg(self.var_gpio_num)
        # if self.read_message() == "ok":
        #     return 1
        # else:
        #     self.__error_except(self.gpio_threshold_write, 1)

    #Read GPIO pin trigger threshold
    # gpio引脚触发阈值读取

    # def gpio_threshold_read(self, name):
    #     self.var_name = name.capitalize()
    #     self.sendMsg("o133?")
    #     self.var_mode_num = self.read_message()
    #     self.var_mode_num1 = self.read_message()
    #     match = re.match('^([\d]+),([\d]+),([\d]+),([\d]+)$', self.var_mode_num)
    #     if match:
    #         if self.var_name == "A0":
    #             return match.group(1)
    #         elif self.var_name == "A1":
    #             return match.group(2)
    #         elif self.var_name == "D0":
    #             return match.group(3)
    #         elif self.var_name == "D1":
    #             return match.group(4)
    #         else:
    #             self.__error_except(self.gpio_threshold_read, 2)
    #     else:
    #         self.__error_except(self.gpio_threshold_read, 3)

    #Write GPIO pin trigger file
    # gpio引脚触发文件写入

    # def gpio_enable_file_write(self, name, num):
    #     self.var_name = name.capitalize()
    #     self.var_num = num
    #     if self.var_name == "A0":
    #         self.var_gpio_num = "o134=" + str(self.var_num) + ",,,"
    #     elif self.var_name == "A1":
    #         self.var_gpio_num = "o134=," + str(self.var_num) + ",,"
    #     elif self.var_name == "D0":
    #         self.var_gpio_num = "o134=,," + str(self.var_num) + ","
    #     elif self.var_name == "D1":
    #         self.var_gpio_num = "o134=,,," + str(self.var_num)
    #     else:
    #         self.__error_except(self.gpio_enable_file_write, 2)
    #     self.sendMsg(self.var_gpio_num)
        # if self.read_message() == "ok":
        #     return 1
        # else:
        #     self.__error_except(self.gpio_enable_file_write, 1)

    #Read GPIO pin trigger file
    # gpio引脚触发文件读取

    # def gpio_enable_file_read(self, name):
    #     self.var_name = name.capitalize()
    #     self.sendMsg("o134?")
    #     self.var_mode_num = self.read_message()
    #     self.var_mode_num1 = self.read_message()
    #     match = re.match('^(.*),(.*),(.*),(.*)$', self.var_mode_num)
    #     if match:
    #         if self.var_name == "A0":
    #             return match.group(1)
    #         elif self.var_name == "A1":
    #             return match.group(2)
    #         elif self.var_name == "D0":
    #             return match.group(3)
    #         elif self.var_name == "D1":
    #             return match.group(4)
    #         else:
    #             self.__error_except(self.gpio_enable_file_read, 2)
    #     else:
    #         self.__error_except(self.gpio_enable_file_read, 3)

    def delay_idle(self):
        if self._block_flag:
            while self.getState()!="Idle":
                    time.sleep(0.1)    

    
if __name__ == "__main__":
    robot = Harobot_UART(block_flag=True,message_flag=True)
    robot.init(serial.Serial('COM4', 115200,timeout=1), -1)
    robot.restart()
    robot.homing()
    robot.pump(1)
    time.sleep(1)
    robot.pump(2)
    time.sleep(1)
    robot.pump(0)
    time.sleep(1)
    robot.writeangle(0,axle1=70)
    robot.writecoordinate(0,0,220)
    robot.zero()


