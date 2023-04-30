# Library imports
from vex import *

class botEnum:
    '''Base class for all enumerated types'''
    value = 0
    name = ""

    def __init__(self, value, name):
        self.value = value
        self.name = name

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

class BotMode:
    '''The measurement units for distance values.'''
    class BotMode(botEnum):
        pass
    DRIVER = BotMode(0, "Driver")
    '''Driver control mode'''
    AUTONEAR = BotMode(1, "AutoNear")
    '''Autonomous Near Field'''
    AUTOFAR = BotMode(2, "AutoFar")
    '''Autonomous Far Field'''

class Bot:
    def __init__(self):
        # Change the botMode to change the behavior
        self.botMode = BotMode.DRIVER
        self.isLongArmOut = False
        self.isAutoRunning = False
        self.isAutoShooting = False
        self.isAutoReady = False
    
    def setup(self):
        self.brain = Brain()
        self.controller = Controller()
        self.setupPortMappings()
        self.setupController()
        self.setupArm()
        self.setupDrive()
        self.setupRocker()
        self.setupSpinner()
        self.setupShooter()
        self.setupHealthLight()

    def setupPortMappings(self):
        self.gyro = Gyro(Ports.PORT10)
        self.motorLeft = Motor(Ports.PORT5)
        self.motorRight = Motor(Ports.PORT7)
        self.driveTrain = None  # Default is DRIVER mode, no driveTrain
        self.rocker = Motor(Ports.PORT12)
        self.shooter = Motor(Ports.PORT4)
        self.arm = Motor(Ports.PORT3)
        self.basketDownBumper = Bumper(Ports.PORT11)
        self.basketUpBumper = Bumper(Ports.PORT2)
        self.healthLight = Touchled(Ports.PORT8)
        self.rockerUpBumper = Bumper(Ports.PORT1)
        self.longArm = Motor(Ports.PORT9)
        self.rockerDownBumper = Bumper(Ports.PORT6)

    def setupController(self):
        self.controller.buttonLUp.pressed(self.onLUp)
        self.controller.buttonLDown.pressed(self.onLDown)
        self.controller.buttonRUp.pressed(self.onRUp)
        self.controller.buttonRDown.pressed(self.onRDown)
        self.controller.buttonRDown.released(self.onRDownReleased)
        self.controller.buttonEUp.pressed(self.onEUp)
        self.controller.buttonEDown.pressed(self.onEDown)
        self.controller.buttonFUp.pressed(self.onFUp)
        self.controller.buttonFDown.pressed(self.onFDown)
        # Delay to make sure events are registered correctly.
        wait(15, MSEC)

    def setupHealthLight(self):
        self.healthLight.set_brightness(100)
        # For autonomous: press the LED button to start 
        self.healthLight.pressed(self.onHealthLightPressed)


    def setupArm(self):
        self.arm.stop()
        self.arm.set_reversed(True)
        self.arm.set_velocity(100, PERCENT)
        self.arm.set_max_torque(100, PERCENT)
        self.arm.set_position(0, DEGREES)

    def setupShooter(self):
        self.shooter.stop()
        # self.shooter.spin(FORWARD)
        self.shooter.set_reversed(True)
        self.shooter.set_stopping(COAST)
        self.shooter.set_max_torque(100, PERCENT)
        self.shooter.set_velocity(67, PERCENT)

    def setupSpinner(self):
        pass

    def setupRocker(self):
        self.rocker.set_reversed(True)
        self.rocker.set_max_torque(100, PERCENT)
        self.rocker.set_velocity(100, PERCENT)
        self.rocker.set_stopping(COAST)
        RockerDown = 0

    def setupDrive(self):
        self.motorLeft.set_velocity(0, PERCENT)
        self.motorLeft.set_max_torque(100, PERCENT)
        self.motorLeft.spin(FORWARD)
        self.motorRight.set_reversed(True)
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
        self.shooter.spin(REVERSE, 100, PERCENT)
        self.rockUpToCatch()

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

    # Experimental: Hold the R-Down bumper and we keep rocking and shooting
    def autoShoot(self, rocks: int = 100):
        while (rocks > 0
                and self.isAutoShooting
                and (self.isAutoRunning or self.driveTrain is None)):
            self.startShooter()
            self.rockUpToCatch()
            self.rockDownToShoot()
            rocks -= 1

    def rockDownToShoot(self):
        print("rockDownToShoot!!")
        if self.rockerDownBumper.pressing():
            return  # The rocker is already down
        
        # Bring the rocker halfway
        if (not self.controller.buttonEUp.pressing()
            and not self.isAutoShooting):
            self.rocker.set_stopping(BRAKE)
            self.rocker.set_timeout(1000, MSEC)
            self.rocker.spin_for(FORWARD, 0.2, TURNS, wait=True)
            self.rocker.stop()
            self.rocker.set_timeout(2000, MSEC)

        # Wait for shooter to spin up IF autoshooting
        self.brain.timer.clear()
        while (self.brain.timer.time(SECONDS) < 2
                and self.isAutoShooting
                and not self.rockerDownBumper.pressing()
                and self.shooter.velocity(PERCENT) > 0.0               
                and self.shooter.velocity(PERCENT) < 30.0):
            print("Velocity: " + str(self.shooter.velocity(PERCENT)))
            wait(30, MSEC)

        self.rocker.spin(FORWARD, 100, PERCENT)
        self.brain.timer.clear()
        while (self.brain.timer.time(SECONDS) < 2
                and not self.rockerDownBumper.pressing()
                and (self.isAutoShooting
                     or self.controller.buttonEUp.pressing())):
            wait(20, MSEC)
        
        self.rocker.set_stopping(BRAKE)
        self.rocker.stop()

        # Experimental: Bounce feature: if you keep holding the button,
        # we can "bounce"
        while (not self.isAutoShooting
                and self.controller.buttonEUp.pressing()):
            print("Bouncing!")
            wait(20, MSEC)

    def rockUpToCatch(self):
        print("rockUpToCatch")
        # If basket is all the way down, raise it a bit
        if self.basketDownBumper.pressing():
            self.arm.set_timeout(2, SECONDS)
            self.arm.spin_for(FORWARD, 1, TURNS)

        # "Pop" if the rocker is already UP to help tumble discs
        '''
        if self.rockerUpBumper.pressing:
            self.rocker.set_velocity(50, PERCENT)
            self.rocker.spin_for(FORWARD, 70, DEGREES)
            wait(1000, MSEC)
            self.rocker.set_velocity(100, PERCENT)
        '''

        self.rocker.spin(REVERSE)
        self.brain.timer.clear()
        while (not self.rockerUpBumper.pressing()
                and self.brain.timer.time(SECONDS) < 2
                and (self.isAutoShooting
                    or not self.controller.buttonEUp.pressing())):
            wait(20, MSEC)
        self.rocker.set_stopping(BRAKE)
        self.rocker.stop()
        
    def toggleLongArm(self):
        self.longArm.set_timeout(3, SECONDS)
        self.longArm.set_max_torque(100, PERCENT)
        if self.isLongArmOut:
            self.isLongArmOut = False 
            self.longArm.set_velocity(75, PERCENT)
            self.longArm.spin(FORWARD)
        else:
            self.isLongArmOut = True
            self.longArm.set_velocity(100, PERCENT)
            self.longArm.spin(REVERSE)

        self.brain.timer.clear()
        while (self.controller.buttonFUp.pressing()
               and self.brain.timer.time(SECONDS) < 4):
            wait(20, MSEC)
        self.longArm.set_stopping(BRAKE)
        self.longArm.stop()

    def stopEverything(self):
        self.rocker.stop()
        self.shooter.set_stopping(COAST)
        self.shooter.stop()
        self.arm.stop()
        if self.driveTrain is not None:
            self.driveTrain.stop()
        self.longArm.stop()
    
    def onLUp(self):
        self.raiseArmBasket(auto=False)

    def onRUp(self):
        self.startSpinner()

    def onLDown(self):
        self.lowerArmBasket(auto=False)

    def onRDownReleased(self):
        self.isAutoShooting = False
        print('Stop autoshooting')

    def onRDown(self):
        # Ignore if both R buttons are pressed at the same time
        if not self.controller.buttonRUp.pressing():
            print("Start autoshooting")
            self.isAutoShooting = True
            self.startShooter()
            self.brain.timer.clear()
            while self.isAutoShooting and self.brain.timer.time(SECONDS) < 1:
                wait(20, MSEC) # Wait and see if button is held down
            self.autoShoot()

    def onEUp(self):
        print("onEUp")
        self.isAutoShooting = False
        self.rockDownToShoot()

    def onEDown(self):
        print("onEDown")
        self.isAutoShooting = False
        self.rockUpToCatch()

    def onFUp(self):
        self.toggleLongArm()

    def onFDown(self):
        self.stopEverything()
        self.shooter.stop()
    
    def autoSetup(self):
        if not self.isAutoReady:
            self.botMode = BotMode.AUTONEAR
            self.isAutoShooting = True

            self.driveTrain = SmartDrive(self.motorLeft, 
                                         self.motorRight,
                                         self.gyro,
                                         wheelTravel=200,
                                         trackWidth=228.6,
                                         wheelBase=(157.1625),
                                         units=DistanceUnits.MM,
                                         externalGearRatio=1)
            self.driveTrain.set_timeout(3, SECONDS)
            self.driveTrain.stop()
            self.driveTrain.set_turn_velocity(80, PERCENT)
            self.driveTrain.set_drive_velocity(90, PERCENT)

            self.brain.screen.print("Preparing...")
            self.brain.screen.next_row()
            wait(100, MSEC)  # Don't calibrate immediately to avoid human touch effects/wobbles
            self.gyro.calibrate()
            self.brain.timer.clear()
            while (self.gyro.is_calibrating() and self.brain.timer.time(SECONDS) < 3):
                wait(20, MSEC)
            self.isAutoReady = True
            self.brain.screen.print("Ready.")
            self.brain.screen.next_row()

            # Set up event handlers for the bumper switches
            # Basket Up Bumper = Auto Near
            # Rocker Up Bumper = Auto Far
            self.basketUpBumper.pressed(self.onBasketUpBumper)

    def onHealthLightPressed(self):
        if self.isAutoRunning:
            # Tell the rest of the code to stop
            self.brain.play_sound(SoundType.POWER_DOWN)
            self.isAutoRunning = False
            self.stopEverything()
        else:
            self.isAutoRunning = True
            self.brain.screen.print("Pressed LED")
            self.brain.screen.next_row()
            self.autoSetup()
            self.isAutoRunning = False

    def onBasketUpBumper(self):
        # This is the best way to stop everything: raise exception
        try:
            self.isAutoRunning = True
            self.autoNear()
        except ValueError as ex:
            self.brain.screen.print("STOPPED")
            self.brain.screen.next_row()

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

    def autoDrive(self, direction, distance, units=DistanceUnits.IN,
                  velocity=None, units_v:VelocityPercentUnits=VelocityUnits.RPM, wait=True):
        if not self.isAutoRunning:
            raise ValueError("Aborted autoDrive")
        self.driveTrain.drive_for(direction,distance, units, velocity, units_v, wait)

    def autoTurn(self, angle, units=RotationUnits.DEG,
                 velocity=None, units_v:VelocityPercentUnits=VelocityUnits.RPM, wait=True):
        if not self.isAutoRunning:
            raise ValueError("Aborted autoTurn")
        self.driveTrain.turn_to_rotation(angle, units, velocity, units_v, wait)

    def autoNear(self):
        if self.driveTrain is not None and self.isAutoRunning:
            if self.isAutoReady:
                self.brain.screen.print("Auto Near GO")
                self.brain.screen.next_row()
            else:
                self.brain.screen.print("Not calibrated yet. Try soon.")
                self.brain.screen.next_row()
                return
                 
            self.autoDrive(REVERSE, 200, MM)
            self.autoTurn(-40, DEGREES)
            self.driveTrain.set_timeout(3, SECONDS)
            self.autoDrive(REVERSE, 780, MM)
            self.autoTurn(-5, DEGREES)
            # Raise arm and approach blue dispenser
            self.driveTrain.set_timeout(3, SECONDS)
            self.arm.spin_for(FORWARD, 300, DEGREES, wait=False)
            self.autoDrive(FORWARD, 220, MM)
            self.autoWiggleBlue()
            self.autoDrive(REVERSE, 220, MM)
            self.autoTurn(35, DEGREES)
            self.autoDrive(REVERSE, 240, MM)
            self.autoTurn(0, DEGREES)
            self.driveTrain.set_drive_velocity(100, PERCENT)
            self.shooter.spin(FORWARD)
            self.autoDrive(REVERSE, 130, MM)
            self.autoShoot(3)
            self.driveTrain.set_timeout(2, SECONDS)
            self.autoDrive(FORWARD, 50, MM)
            self.autoDrive(REVERSE, 70, MM)
            self.autoShoot(7)

    def autoFar(self):
        if self.driveTrain is not None and self.isAutoRunning:
            if self.isAutoReady:
                self.brain.screen.print("Auto Far GO")
                self.brain.screen.next_row()
            else:
                self.brain.screen.print("Not calibrated yet. Try soon.")
                self.brain.screen.next_row()
                return
            
            self.autoDrive(REVERSE, 200, MM)
            self.autoTurn(36, DEGREES)
            self.driveTrain.set_timeout(10, SECONDS)
            self.autoDrive(REVERSE, 820, MM)
            self.autoTurn(0, DEGREES)
            self.driveTrain.set_timeout(3, SECONDS)
            self.arm.spin_for(FORWARD, 300, DEGREES, wait=False)
            self.autoDrive(FORWARD, 255, MM)
            self.autoWiggleBlue()
            self.autoDrive(REVERSE, 220, MM)
            self.autoTurn(-40, DEGREES)
            self.autoDrive(REVERSE, 200, MM)
            self.autoTurn(-8, DEGREES)
            self.driveTrain.set_drive_velocity(100, PERCENT)
            self.shooter.spin(FORWARD)
            self.autoDrive(REVERSE, 130, MM)
            self.autoShoot(4)
            self.shooter.stop()
            self.autoPushYellowFromFar()

    def autoPushYellowFromFar(self):
        if self.driveTrain is not None:
            self.driveTrain.turn_for(LEFT, 95, DEGREES)
            self.autoDrive(FORWARD, 200, MM)
            self.driveTrain.turn_for(RIGHT, 30, DEGREES)
            self.autoDrive(FORWARD, 200, MM)

    def autoWiggleBlue(self):
        # Wiggle forward and back to help tilt discs in
        if self.driveTrain is not None:
            self.arm.spin_for(REVERSE, 300, DEGREES, wait=False)
            wait(1.5, SECONDS)
            self.driveTrain.set_timeout(2, SECONDS)
            self.autoDrive(FORWARD, 30, MM)
            self.autoDrive(REVERSE, 40, MM)
            self.autoDrive(FORWARD, 80, MM)

    def run(self):
        self.setup()
        while True: # Main loop handling drive train updates
            if self.botMode == BotMode.DRIVER:
                self.updateLeftDrive(1)
                self.updateRightDrive(1)
            self.checkHealth()
            wait(20, MSEC)  # Yield to other things going on

bot = Bot()
bot.run()
