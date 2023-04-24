# Library imports
from vex import *


class Bot:
    def __init__(self):
        self.slot = 0  # What slot to put this program in
        self.isLongArmOut = False
        self.brain = Brain()
        self.controller = Controller()
        self.setupPortMappings()
        self.setupArm()
        self.setupDrive()
        self.setupRocker()
        self.setupSpinner()
        self.setupShooter()
        self.setupController()
        self.setupHealthLight()

    def setupPortMappings(self):
        self.motorLeft = Motor(Ports.PORT5)
        self.motorRight = Motor(Ports.PORT7)
        self.rocker = Motor(Ports.PORT12)
        self.shooter = Motor(Ports.PORT4)
        self.arm = Motor(Ports.PORT3)
        self.basketDownBumper = Bumper(Ports.PORT11)
        self.basketUpBumper = Bumper(Ports.PORT2)
        self.healthLight = Touchled(Ports.PORT8)
        self.rockerUpBumper = Bumper(Ports.PORT1)
        self.longArm = Motor(Ports.PORT9)
        self.rockerDownBumper = Bumper(Ports.PORT6)

    def setupHealthLight(self):
        self.healthLight.set_brightness(100)

    def setupArm(self):
        self.arm.stop()
        self.arm.set_velocity(100, PERCENT)
        self.arm.set_max_torque(100, PERCENT)
        self.arm.set_position(0, DEGREES)

    def setupShooter(self):
        self.shooter.stop()
        self.shooter.spin(FORWARD)
        self.shooter.set_stopping(COAST)
        self.shooter.set_max_torque(100, PERCENT)
        self.shooter.set_velocity(90, PERCENT)

    def setupSpinner(self):
        pass

    def setupRocker(self):
        self.rocker.set_max_torque(100, PERCENT)
        self.rocker.set_velocity(100, PERCENT)
        self.rocker.set_stopping(COAST)
        RockerDown = 0

    def setupDrive(self):
        self.motorLeft.set_velocity(0, PERCENT)
        self.motorLeft.set_max_torque(100, PERCENT)
        self.motorLeft.spin(FORWARD)
        self.motorRight.set_velocity(0, PERCENT)
        self.motorRight.set_max_torque(100, PERCENT)
        self.motorRight.spin(FORWARD)

    def updateLeftDrive(self, joystickTolerance: int):
        velocity: float = self.controller.axisA.position()
        if math.fabs(velocity) > joystickTolerance:
            self.motorLeft.set_velocity(velocity, PERCENT)
        else:
            self.motorLeft.set_velocity(0, PERCENT)

    def updateRightDrive(self, joystickTolerance: int):
        velocity: float = self.controller.axisD.position()
        if math.fabs(velocity) > joystickTolerance:
            self.motorRight.set_velocity(velocity, PERCENT)
        else:
            self.motorRight.set_velocity(0, PERCENT)

    def raiseArmBasket(self, auto: bool = False):
        self.brain.timer.clear()
        # Do not let the motor for the arm basket spin too long
        # and only until the bumper sensor is pressed
        while (self.brain.timer.time(SECONDS) < 4
                and not self.basketUpBumper.pressing()
                and (auto or self.controller.buttonLUp.pressing())):
            self.arm.spin(FORWARD)
            wait(20, MSEC)
        self.arm.set_stopping(HOLD)
        self.arm.stop()

    def startSpinner(self):
        self.brain.play_sound(SoundType.WRONG_WAY)
        self.brain.play_note(3, 6, 1000)
        self.shooter.spin(REVERSE)
        self.rockDown(auto=True)

    def startShooter(self):
        self.shooter.spin(FORWARD)

    def lowerArmBasket(self, auto: bool = False):
        self.brain.timer.clear()
        while (self.brain.timer.time(SECONDS) < 4
                and not self.basketDownBumper.pressing()
                and (auto or self.controller.buttonLDown.pressing())):
            self.arm.spin(REVERSE)
            wait(20, MSEC)
        self.arm.set_stopping(BRAKE)
        self.arm.stop()

    def rockUp(self, auto: bool = False):
        self.rocker.set_velocity(100, PERCENT)
        self.rocker.spin(FORWARD)
        self.brain.timer.clear()
        while not not (self.brain.timer.time(SECONDS) < 3
                       and (auto or self.controller.buttonEUp.pressing())):
            wait(20, MSEC)
        self.rocker.set_stopping(HOLD)
        self.rocker.stop()

    def rockDown(self, auto: bool = False):
        # If basket is all the way down, raise it a bit
        if self.basketDownBumper.pressing():
            self.arm.set_timeout(2, SECONDS)
            self.arm.spin_for(FORWARD, 1, TURNS)
            self.brain.play_sound(SoundType.FILLUP)

        self.brain.timer.clear()
        while (not self.rockerUpBumper.pressing()
                and self.brain.timer.time(SECONDS) < 3
                and ((auto or self.controller.buttonEDown.pressing()
                     and not self.controller.buttonEUp.pressing()))):
            self.rocker.spin(REVERSE)
            wait(20, MSEC)
        self.rocker.set_stopping(BRAKE)
        self.rocker.stop()

    def toggleLongArm(self):
        self.longArm.set_timeout(3, SECONDS)
        self.longArm.set_max_torque(100, PERCENT)
        if not self.isLongArmOut:
            self.isLongArmOut = True
            self.longArm.set_velocity(100, PERCENT)
            self.longArm.spin(REVERSE)
            self.longArm.set_stopping(BRAKE)
        else:
            self.isLongArmOut = False
            self.longArm.set_velocity(75, PERCENT)
            self.longArm.spin(FORWARD)
            self.longArm.set_stopping(BRAKE)
        self.brain.timer.clear()
        while (self.controller.buttonFUp.pressing()
               and self.brain.timer.time(SECONDS) > 4):
            wait(20, MSEC)
        self.longArm.set_stopping(BRAKE)
        self.longArm.stop()

    def stopRockAndShoot(self):
        self.rocker.stop()
        self.shooter.set_stopping(COAST)
        self.shooter.stop()

    def onLUp(self):
        self.raiseArmBasket(auto=False)

    def onLDown(self):
        self.lowerArmBasket(auto=False)

    def onRUp(self):
        self.startSpinner()

    def onRDown(self):
        if not self.controller.buttonRUp.pressing():
            self.startShooter()

    def onEUp(self):
        self.rockUp(auto=False)

    def onEDown(self):
        self.rockDown(auto=False)

    def onFUp(self):
        self.toggleLongArm()

    def onFDown(self):
        self.stopRockAndShoot()
        self.shooter.stop()

    def setupController(self):
        self.controller.buttonLUp.pressed(self.onLUp)
        self.controller.buttonLDown.pressed(self.onLDown)
        self.controller.buttonRUp.pressed(self.onRUp)
        self.controller.buttonRDown.pressed(self.onRDown)
        self.controller.buttonEUp.pressed(self.onEUp)
        self.controller.buttonEDown.pressed(self.onEDown)
        self.controller.buttonFUp.pressed(self.onFUp)
        self.controller.buttonFDown.pressed(self.onFDown)
        # self.rockerDownBumper.pressed(onevent_RockerDownBumper_pressed_0)
        # add 15ms delay to make sure events are registered correctly.
        wait(15, MSEC)

    def checkHealth(self):
        color = Color.RED
        capacity = self.brain.battery.capacity()
        if capacity > 85:
            color = Color.GREEN
        elif capacity > 75:
            color = Color.BLUE
        elif capacity > 60:
            color = Color.ORANGE
        else:
            color = Color.RED
        self.healthLight.set_color(color)

    def run(self):
        self.setupController()
        if self.slot == 2:   # Auton
            # AutoShootBlue_near(True)
            pass
        elif self.slot == 3: # Auton
            # AutoShootBlue_near(False)
            pass
        else:
            # Main loop
            while True:
                self.updateLeftDrive(1)
                self.updateRightDrive(1)
                self.checkHealth()
                wait(20, MSEC)  # Yield to other things going on

