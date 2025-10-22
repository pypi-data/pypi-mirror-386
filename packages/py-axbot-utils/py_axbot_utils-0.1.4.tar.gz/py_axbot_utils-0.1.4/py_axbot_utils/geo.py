import math
from typing import List, Union

from geometry_msgs.msg import Point as PointMsg
from geometry_msgs.msg import Pose as PoseMsg
from geometry_msgs.msg import PoseStamped, PoseWithCovarianceStamped
from geometry_msgs.msg import Quaternion as QuaternionMsg
from geometry_msgs.msg import Vector3 as Vector3Msg


class Vector2:
    def __init__(self, x=0.0, y=0.0) -> None:
        self.x = x
        self.y = y

    def to_ros(self) -> Vector3Msg:
        v = Vector3Msg(x=self.x, y=self.y, z=0)
        return v

    def to_ros_point(self) -> PointMsg:
        v = PointMsg(x=self.x, y=self.y, z=0)
        return v

    # rotate a 2d vector counter-clockwise
    def rotate(self, angle) -> "Vector2":
        c = math.cos(angle)
        s = math.sin(angle)
        return Vector2(c * self.x - s * self.y, s * self.x + c * self.y)

    @property
    def length(self) -> float:
        return math.sqrt(self.x * self.x + self.y * self.y)

    def __str__(self):
        return f"Vector2({self.x}, {self.y})"

    def __repr__(self):
        return str(self)

    def __add__(self, r: "Vector2"):
        return Vector2(self.x + r.x, self.y + r.y)

    def __sub__(self, r: "Vector2"):
        return Vector2(self.x - r.x, self.y - r.y)

    def __eq__(self, r: "Vector2"):
        return r != None and self.x == r.x and self.y == r.y

    def __neg__(self):
        return Vector2(-self.x, -self.y)

    def __mul__(self, r: float):
        return Vector2(self.x * r, self.y * r)

    def __rmul__(self, r: float):
        return Vector2(self.x * r, self.y * r)

    def __truediv__(self, r: float):
        return Vector2(self.x / r, self.y / r)


class Vector3:
    def __init__(self, x=0.0, y=0.0, z=0.0) -> None:
        self.x = x
        self.y = y
        self.z = z

    @staticmethod
    def from_ros(msg: Vector3Msg) -> "Vector3":
        return Vector3(msg.x, msg.y, msg.z)

    def to_ros(self) -> Vector3Msg:
        v = Vector3Msg(x=self.x, y=self.y, z=self.z)
        return v

    def to_ros_point(self) -> PointMsg:
        v = PointMsg(x=self.x, y=self.y, z=self.z)
        return v

    def to_vector2(self):
        return Vector2(self.x, self.y)

    @property
    def length(self) -> float:
        return math.sqrt(self.x * self.x + self.y * self.y + self.z * self.x)

    def __str__(self):
        return f"Vector3({self.x}, {self.y}, {self.z})"

    def __repr__(self):
        return str(self)

    def __add__(self, r: "Vector3"):
        return Vector3(self.x + r.x, self.y + r.y, self.z + r.z)

    def __sub__(self, r: "Vector3"):
        return Vector3(self.x - r.x, self.y - r.y, self.z - r.z)

    def __eq__(self, r: "Vector3"):
        return r != None and self.x == r.x and self.y == r.y and self.z == r.z

    def __neg__(self):
        return Vector3(-self.x, -self.y, -self.z)

    def __mul__(self, r: float):
        return Vector3(self.x * r, self.y * r, self.z * r)

    def __rmul__(self, r: float):
        return Vector3(self.x * r, self.y * r, self.z * r)

    def __truediv__(self, r: float):
        return Vector3(self.x / r, self.y / r, self.z / r)


class RollPitchYaw:
    def __init__(self, r, p, y) -> None:
        self.roll = r
        self.pitch = p
        self.yaw = y

    def __eq__(self, r: "RollPitchYaw"):
        return (
            r != None
            and self.roll == r.roll
            and self.pitch == r.pitch
            and self.yaw == r.yaw
        )

    def __str__(self):
        return f"RollPitchYaw({self.roll}, {self.pitch}, {self.yaw})"

    def __repr__(self):
        return str(self)


class Quaternion:
    def __init__(self, x=0.0, y=0.0, z=0.0, w=1.0) -> None:
        self.x = x
        self.y = y
        self.z = z
        self.w = w

    @staticmethod
    def identity() -> "Quaternion":
        return Quaternion(0, 0, 0, 1)

    @staticmethod
    def from_xyzw(x, y, z, w) -> "Quaternion":
        q = Quaternion()
        q.x = x
        q.y = y
        q.z = z
        q.w = w
        return q

    @staticmethod
    def from_rpy(roll: Union[RollPitchYaw, float], pitch=None, yaw=None):
        q = Quaternion()

        if isinstance(roll, RollPitchYaw):
            pitch = roll.pitch
            yaw = roll.yaw
            roll = roll.roll

        sin_roll = math.sin(roll / 2)
        cos_pitch = math.cos(pitch / 2)
        cos_yaw = math.cos(yaw / 2)
        cos_roll = math.cos(roll / 2)
        sin_pitch = math.sin(pitch / 2)
        sin_yaw = math.sin(yaw / 2)

        q.x = sin_roll * cos_pitch * cos_yaw - cos_roll * sin_pitch * sin_yaw
        q.y = cos_roll * sin_pitch * cos_yaw + sin_roll * cos_pitch * sin_yaw
        q.z = cos_roll * cos_pitch * sin_yaw - sin_roll * sin_pitch * cos_yaw
        q.w = cos_roll * cos_pitch * cos_yaw + sin_roll * sin_pitch * sin_yaw

        return q

    def to_ros(self) -> QuaternionMsg:
        q = QuaternionMsg(x=self.x, y=self.y, z=self.z, w=self.w)
        return q

    def to_rpy(self) -> RollPitchYaw:
        """
        Convert a quaternion into euler angles (roll, pitch, yaw)
        roll is rotation around x in radians (counterclockwise)
        pitch is rotation around y in radians (counterclockwise)
        yaw is rotation around z in radians (counterclockwise)
        """
        t0 = +2.0 * (self.w * self.x + self.y * self.z)
        t1 = +1.0 - 2.0 * (self.x * self.x + self.y * self.y)
        roll_x = math.atan2(t0, t1)

        t2 = +2.0 * (self.w * self.y - self.z * self.x)
        t2 = +1.0 if t2 > +1.0 else t2
        t2 = -1.0 if t2 < -1.0 else t2
        pitch_y = math.asin(t2)

        t3 = +2.0 * (self.w * self.z + self.x * self.y)
        t4 = +1.0 - 2.0 * (self.y * self.y + self.z * self.z)
        yaw_z = math.atan2(t3, t4)

        return RollPitchYaw(roll_x, pitch_y, yaw_z)  # in radians

    @property
    def yaw(self):
        return self.to_rpy().yaw

    def inverse(self):
        return Quaternion(self.x, self.y, self.z, -self.w)

    def transform_vector(self, v: Vector3):
        num12 = self.x + self.x
        num2 = self.y + self.y
        num = self.z + self.z
        num11 = self.w * num12
        num10 = self.w * num2
        num9 = self.w * num
        num8 = self.x * num12
        num7 = self.x * num2
        num6 = self.x * num
        num5 = self.y * num2
        num4 = self.y * num
        num3 = self.z * num
        num15 = ((v.x * ((1.0 - num5) - num3)) + (v.y * (num7 - num9))) + (
            v.z * (num6 + num10)
        )
        num14 = ((v.x * (num7 + num9)) + (v.y * ((1.0 - num8) - num3))) + (
            v.z * (num4 - num11)
        )
        num13 = ((v.x * (num6 - num10)) + (v.y * (num4 + num11))) + (
            v.z * ((1.0 - num8) - num5)
        )

        return Vector3(num15, num14, num13)

    def __mul__(self, r: "Quaternion" or Vector3 or "Pose3"):
        if isinstance(r, Vector3):
            return self.transform_vector(r)
        elif isinstance(r, Quaternion):
            return Quaternion(
                self.x * r.w + self.y * r.z - self.z * r.y + self.w * r.x,
                -self.x * r.z + self.y * r.w + self.z * r.x + self.w * r.y,
                self.x * r.y - self.y * r.x + self.z * r.w + self.w * r.z,
                -self.x * r.x - self.y * r.y - self.z * r.z + self.w * r.w,
            )
        elif isinstance(r, Pose3):
            return Pose3(pos=self.transform_vector(r.pos), ori=self * r.ori)

        raise TypeError(f"Quaternion can't multiple with {type(r)}")

    def __eq__(self, r: "Quaternion"):
        return (
            r != None
            and self.x == r.x
            and self.y == r.y
            and self.z == r.z
            and self.w == r.w
        )

    def __str__(self):
        return f"Quaternion({self.x}, {self.y}, {self.z}, {self.w})"

    def __repr__(self):
        return str(self)


class Pose2:
    __init_pos = Vector2(0, 0)

    def __init__(self, pos: Vector2 = __init_pos, ori=0.0) -> None:
        if pos is Pose2.__init_pos:
            self.pos = Vector2(0, 0)
        else:
            self.pos = pos

        self.ori = ori

    def to_ros(self) -> PoseMsg:
        msg = PoseMsg(self.pos.to_ros(), Quaternion.from_rpy(0, 0, self.ori))
        return msg

    def inverse(self):
        return Pose2((-self.pos).rotate(-self.ori), -self.ori)

    def transform_vector(self, v: Vector2) -> Vector2:
        return v.rotate(self.ori) + self.pos

    def __str__(self):
        return f"Pose2(x = {self.pos.x}, y = {self.pos.y}, ori = {self.ori})"

    def __mul__(self, r: "Pose2"):
        return Pose2(pos=self.pos + r.pos.rotate(self.ori), ori=self.ori + r.ori)

    def __eq__(self, r: "Pose2"):
        return r != None and self.pos == r.pos and self.ori == r.ori


class Pose3:
    __init_pos = Vector3(0, 0, 0)

    def __init__(self, pos: Vector3 = __init_pos, ori: "Quaternion" = 0) -> None:
        if pos is Pose3.__init_pos:
            self.pos = Vector3(0, 0, 0)
        else:
            self.pos = pos

        if isinstance(ori, Quaternion):
            self.ori = ori
        else:
            self.ori = Quaternion(0, 0, 0, 1)

    @staticmethod
    def from_pose2(pose2: Pose2) -> "Pose3":
        return Pose3(
            Vector3(pose2.pos.x, pose2.pos.y, 0), Quaternion.from_rpy(0, 0, pose2.ori)
        )

    @staticmethod
    def from_ros(msg: PoseMsg or PoseWithCovarianceStamped or PoseStamped) -> "Pose3":
        pose: PoseMsg = None
        if isinstance(msg, PoseWithCovarianceStamped):
            msg: PoseWithCovarianceStamped
            pose = msg.pose.pose
        elif isinstance(msg, PoseStamped):
            msg: PoseStamped
            pose = msg.pose
        elif isinstance(msg, PoseMsg):
            pose = msg
        else:
            raise TypeError(f"Can't convert {type(msg)} into Pose3")

        return Pose3(
            Vector3(pose.position.x, pose.position.y, pose.position.z),
            Quaternion.from_xyzw(
                pose.orientation.x,
                pose.orientation.y,
                pose.orientation.z,
                pose.orientation.w,
            ),
        )

    def to_ros(self) -> PoseMsg:
        msg = PoseMsg(self.pos.to_ros(), self.ori.to_ros())
        return msg

    def to_pose2(self) -> Pose2:
        return Pose2(self.pos.to_vector2(), self.ori.yaw)

    def inverse(self):
        ori_inv = self.ori.inverse()
        return Pose3(ori_inv * -self.pos, ori_inv)

    def __str__(self):
        return f"Pose3({self.pos}, {self.ori})"

    def __repr__(self):
        return str(self)

    def transform_vector(self, v: Vector3) -> Vector3:
        return self.ori.transform_vector(v) + self.pos

    def __mul__(self, r: Union["Pose3", Vector3]):
        if isinstance(r, Vector3):
            return self.ori.transform_vector(r) + self.pos
        return Pose3(
            pos=self.pos + self.ori.transform_vector(r.pos), ori=self.ori * r.ori
        )

    def __eq__(self, r: "Pose3"):
        return r != None and self.pos == r.pos and self.ori == r.ori


def polygon_inside(poly: List, x: float, y: float):
    points_count = len(poly)
    if points_count < 2:
        return False

    inside = False

    p1x, p1y = poly[0]
    for i in range(points_count + 1):
        p2x, p2y = poly[i % points_count]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        x_intersects = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= x_intersects:
                        inside = not inside
        p1x, p1y = p2x, p2y

    return inside
