#! usr/bin/python3.9
"""
    Module initially auto generated using V5Automation files from CATIA V5 R28 on 2020-07-06 14:02:20.222384

    .. warning::
        The notes denoted "CAA V5 Visual Basic Help" are to be used as reference only.
        They are there as a guide as to how the visual basic / catscript functions work
        and thus help debugging in pycatia.
        
"""

from pycatia.mec_mod_interfaces.hybrid_shape import HybridShape


class Plane(HybridShape):
    """
        .. note::
            :class: toggle

            CAA V5 Visual Basic Help (2020-07-06 14:02:20.222384)

                | System.IUnknown
                |     System.IDispatch
                |         System.CATBaseUnknown
                |             System.CATBaseDispatch
                |                 System.AnyObject
                |                     MecModInterfaces.HybridShape
                |                         Plane
                | 
                | Represents the hybrid shape Plane feature object.
                | Role: Declare hybrid shape Plane root feature object. All interfaces for
                | different type of Plane derives HybridShapePlane.
                | 
                | Use the CATIAHybridShapeFactory to create a HybridShapePlane
                | objects.
                | 
                | See also:
                |     HybridShapeFactory
    
    """

    def __init__(self, com_object):
        super().__init__(com_object)
        self.plane_ = com_object

    def get_first_axis(self) -> tuple[float, float, float]:
        """
        .. note::
            :class: toggle

            CAA V5 Visual Basic Help (2020-07-06 14:02:20.222384))
                | o Sub GetFirstAxis(CATSafeArrayVariant oFirstAxis)
                | 
                |     Returns the coordinates of the first plane axis.
                | 
                |     Parameters:
                | 
                |         oFirstAxis[0]
                |             The X Coordinate of the first plane axis 
                |         oFirstAxis[1]
                |             The Y Coordinate of the first plane axis 
                |         oFirstAxis[2]
                |             The Z Coordinate of the first plane axis 
                | 
                |     See also:
                |         HybridShapeFactory

        :rtype: tuple[float,float,float]
        """
        vba_function_name = 'wrapper_get_first_axis'
        vba_code = f"""
        Public Function {vba_function_name}(oPlane As Plane)
            Dim aReturn(2) as Variant
            oPlane.GetFirstAxis aReturn
            {vba_function_name} = aReturn
        End Function
        """

        return self.application.system_service.evaluate(vba_code, 0, vba_function_name, [self.com_object])

    def get_origin(self) -> tuple[float, float, float]:
        """
        .. note::
            :class: toggle

            CAA V5 Visual Basic Help (2020-07-06 14:02:20.222384))
                | o Sub GetOrigin(CATSafeArrayVariant oOrigin)
                | 
                |     Returns the origin of the plane.
                | 
                |     Parameters:
                | 
                |         oOrigin[0]
                |             The X Coordinate of the plane origin 
                |         oOrigin[1]
                |             The Y Coordinate of the plane origin 
                |         oOrigin[2]
                |             The Z Coordinate of the plane origin 
                | 
                |     See also:
                |         HybridShapeFactory

        :rtype: tuple[float, float, float]
        """

        vba_function_name = 'wrapper_get_origin'
        vba_code = f"""
        Public Function {vba_function_name}(oPlane As Plane)
            Dim aReturn(2) as Variant
            oPlane.GetOrigin aReturn
            {vba_function_name} = aReturn
        End Function
        """

        return self.application.system_service.evaluate(vba_code, 0, vba_function_name, [self.com_object])

    def get_position(self) -> tuple[float, float, float]:
        """
        .. note::
            :class: toggle

            CAA V5 Visual Basic Help (2020-07-06 14:02:20.222384))
                | o Sub GetPosition(double oX,
                | double oY,
                | double oZ)
                | 
                |     Gets the position where the plane is displayed.
                | 
                |     Parameters:
                | 
                |         oX
                |             X coordinates 
                |         oY
                |             Y coordinates 
                |         oZ
                |             Z coordinates 
                | 
                |     Returns:
                |         S_OK if the position has been set before, E_FAIL else.

        :rtype: tuple[float, float, float]
        """

        vba_function_name = 'wrapper_get_position'
        vba_code = f"""
        Public Function {vba_function_name}(oPlane As Plane)
            Dim aReturn(2) As Variant
            x_pos = 0.0
            y_pos = 0.0
            z_pos = 0.0
            On Error Resume Next
            oPlane.GetPosition x_pos, y_pos, z_pos
            If Err.Number <> 0 Then
                Err.Clear
            End If
            aReturn(0) = x_pos
            aReturn(1) = y_pos
            aReturn(2) = z_pos
            {vba_function_name} = aReturn
        End Function
        """

        return self.application.system_service.evaluate(vba_code, 0, vba_function_name, [self.com_object])

    def get_second_axis(self) -> tuple[float, float, float]:
        """
        .. note::
            :class: toggle

            CAA V5 Visual Basic Help (2020-07-06 14:02:20.222384))
                | o Sub GetSecondAxis(CATSafeArrayVariant oSecondAxis)
                | 
                |     Returns the coordinates of the second plane axis.
                | 
                |     Parameters:
                | 
                |         oSecondAxis[0]
                |             The X Coordinate of the second plane axis 
                |         oSecondAxis[1]
                |             The Y Coordinate of the second plane axis 
                |         oSecondAxis[2]
                |             The Z Coordinate of the second plane axis 
                | 
                |     See also:
                |         HybridShapeFactory

        :rtype: tuple[float,float,float]
        """
        vba_function_name = 'wrapper_get_second_axis'
        vba_code = f"""
        Public Function {vba_function_name}(oPlane As Plane)
            Dim aReturn(2) As Variant
            oPlane.GetSecondAxis aReturn
            {vba_function_name} = aReturn
        End Function
        """

        return self.application.system_service.evaluate(vba_code, 0, vba_function_name, [self.com_object])

    def is_a_ref_plane(self) -> int:
        """
        .. note::
            :class: toggle

            CAA V5 Visual Basic Help (2020-07-06 14:02:20.222384))
                | o Func IsARefPlane() As long
                | 
                |     Queries whether the plane is a reference plane (fixed axis
                |     plane).
                | 
                |     Returns:
                |         0 when the plane is a reference plane, 1 else.

        :rtype: int
        """
        return self.plane_.IsARefPlane()

    def put_first_axis(self, i_first_axis: tuple) -> None:
        """
        .. note::
            :class: toggle

            CAA V5 Visual Basic Help (2020-07-06 14:02:20.222384))
                | o Sub PutFirstAxis(CATSafeArrayVariant iFirstAxis)
                | 
                |     Sets the first axis. The first plane axis must be a point-direction
                |     line.
                |     Note: This method can only be used on CATIAHybridShapePlane2Lines
                |     feature
                | 
                |     Parameters:
                | 
                |         iFirstAxis[0]
                |             The X Coordinate of the first plane axis 
                |         iFirstAxis[1]
                |             The Y Coordinate of the first plane axis 
                |         iFirstAxis[2]
                |             The Z Coordinate of the first plane axis 
                | 
                |     See also:
                |         HybridShapeFactory

        :param tuple i_first_axis:
        :rtype: None
        """

        return self.plane_.PutFirstAxis(i_first_axis)

        # vba_function_name = 'wrapper_put_first_axis'
        # vba_code = f"""
        # Public Function {vba_function_name}(oPlane, input_axis)
        #     Dim iFirstAxis(2)
        #     iFirstAxis(0) = input_axis(0)
        #     iFirstAxis(1) = input_axis(0)
        #     iFirstAxis(2) = input_axis(0)
        #     oPlane.PutFirstAxis(iFirstAxis)
        #     {vba_function_name} = iFirstAxis
        # End Function
        # """
        #
        # system_service = self.application.system_service
        # return system_service.evaluate(vba_code, 0, vba_function_name, [self.plane_, i_first_axis])

    def put_origin(self, i_origin: tuple) -> None:
        """
        .. note::
            :class: toggle

            CAA V5 Visual Basic Help (2020-07-06 14:02:20.222384))
                | o Sub PutOrigin(CATSafeArrayVariant iOrigin)
                | 
                |     Sets the origin of the plane.
                |     Note: This method can only be used on CATIAHybridShapePlane2Lines
                |     feature
                | 
                |     Parameters:
                | 
                |         iOrigin[0]
                |             The X Coordinate of the plane origin 
                |         iOrigin[1]
                |             The Y Coordinate of the plane origin 
                |         iOrigin[2]
                |             The Z Coordinate of the plane origin 
                | 
                |     See also:
                |         HybridShapeFactory

        :param tuple i_origin:
        :rtype: None
        """

        # return self.plane_.PutOrigin(i_origin)

        # # The following is one of my many attempts to get this to work.
        # # It's not happening for now ....
        # vba_function_name = 'wrapper_put_origin'
        # vba_code = f"""
        # Public Function {vba_function_name}(oPlane, i_origin as Variant)
        #     On Error Resume Next
        #     oPlane.PutOrigin i_origin
        #     If Err.Number <> 0 Then
        #         Err.Clear
        #     End If
        #     {vba_function_name} = i_origin
        # End Function
        # """
        #
        # system_service = self.application.system_service
        # return system_service.evaluate(vba_code, 0, vba_function_name, [self.plane_, i_origin])

    def put_second_axis(self, i_second_axis: tuple) -> None:
        """
        .. note::
            :class: toggle

            CAA V5 Visual Basic Help (2020-07-06 14:02:20.222384))
                | o Sub PutSecondAxis(CATSafeArrayVariant iSecondAxis)
                | 
                |     Sets the coordinates of the second plane axis. The second plane axis must
                |     be a point-direction line
                |     Note: This method can only be used on CATIAHybridShapePlane2Lines
                |     feature
                | 
                |     Parameters:
                | 
                |         iSecondAxis[0]
                |             The X Coordinate of the second plane axis 
                |         iSecondAxis[1]
                |             The Y Coordinate of the second plane axis 
                |         iSecondAxis[2]
                |             The Z Coordinate of the second plane axis 
                | 
                |     See also:
                |         HybridShapeFactory

        :param tuple i_second_axis:
        :rtype: None
        """
        return self.plane_.PutSecondAxis(i_second_axis)
        # # # # Autogenerated comment: 
        # # some methods require a system service call as the methods expects a vb array object
        # # passed to it and there is no way to do this directly with python. In those cases the following code
        # # should be uncommented and edited accordingly. Otherwise completely remove all this.
        # # vba_function_name = 'put_second_axis'
        # # vba_code = """
        # # Public Function put_second_axis(plane)
        # #     Dim iSecondAxis (2)
        # #     plane.PutSecondAxis iSecondAxis
        # #     put_second_axis = iSecondAxis
        # # End Function
        # # """

        # # system_service = self.application.system_service
        # # return system_service.evaluate(vba_code, 0, vba_function_name, [self.com_object])

    def remove_position(self) -> None:
        """
        .. note::
            :class: toggle

            CAA V5 Visual Basic Help (2020-07-06 14:02:20.222384))
                | o Sub RemovePosition()
                | 
                |     Removes reference position of a plane.
                |     Note: When removed, the plane is displayed at its default position.

        :rtype: None
        """
        return self.plane_.RemovePosition()

    def set_position(self, i_x: float, i_y: float, i_z: float) -> None:
        """
        .. note::
            :class: toggle

            CAA V5 Visual Basic Help (2020-07-06 14:02:20.222384))
                | o Sub SetPosition(double iX,
                | double iY,
                | double iZ)
                | 
                |     Sets the position where the plane is displayed.
                | 
                |     Parameters:
                | 
                |         iX
                |             X coordinates 
                |         iY
                |             Y coordinates 
                |         iZ
                |             Z coordinates

        :param float i_x:
        :param float i_y:
        :param float i_z:
        :rtype: None
        """
        return self.plane_.SetPosition(i_x, i_y, i_z)

    def __repr__(self):
        return f'Plane(name="{self.name}")'
