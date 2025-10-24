

'''
Create an Hexagonal joint for two surfaces
'''

def hexSnapFeature(self, H, R, tol, angle = 0,  kind = 'M'):
    
    def _maleSnap(loc):
        snap = (cq.Workplane()
                .sketch()
                .regularPolygon(R, 6, angle = angle)
                .finalize()
                .extrude(H)
                .edges('|Z')
                .fillet(2*tol)
                .faces(">Z")
                .workplane(offset = -H/3 + tol).tag('top')
                .polarArray(R*math.sqrt(3)/2, 0, 360, 6)
                .eachpoint(lambda loc: (cq.Workplane('XZ')
                                        .lineTo(0, H/3 - tol)
                                        .lineTo(tol, 0)
                                        .lineTo(0, -H/3 + tol)
                                        .close()
                                        .extrude(math.sqrt(3)*R/4-2*tol)
                                        .edges("|Z and <Y")
                                        .workplane(centerOption= 'CenterOfMass')
                                        .transformed(rotate = cq.Vector(0,60,0))
                                        .split(keepBottom = True)
                                        .mirror('XZ', union = True)
                                        .val()
                                        .locate(loc)
                                        )
                           ,combine = 'a'
                           )
                )
        return snap.val().locate(loc)
    
    def _femaleSnap(loc):
        radius = R+tol
        snap = (cq.Workplane()
                .sketch()
                .regularPolygon(radius, 6, angle = angle)
                .finalize()
                .extrude(-H)
                .edges('|Z')
                .fillet(tol)
                .faces("<Z")
                .workplane(offset = H/3 - tol, invert = True).tag('bottom')
                .polarArray(radius*math.sqrt(3)/2, 0, 360, 6)
                .eachpoint(lambda loc: (cq.Workplane('XZ')
                                        .lineTo(0, H/3 - tol)
                                        .lineTo(-tol, 0)
                                        .lineTo(0, -H/3 + tol)
                                        .close()
                                        .extrude(math.sqrt(3)*R/4 -2*tol)
                                        .edges("|Z and <Y")
                                        .workplane(centerOption= 'CenterOfMass')
                                        .transformed(rotate = cq.Vector(0,-60,0))
                                        .split(keepBottom = True)
                                        .mirror('XZ', union = True)
                                        .val()
                                        .locate(loc)
                                        )
                           ,combine = 's'
                           )
                )
        return snap.val().locate(loc)
    
    if kind == 'M':
        return self.eachpoint(_maleSnap, combine = 'a')
    else:
        return self.eachpoint(_femaleSnap, combine = 's')


# include the new function to cadquery
cq.Workplane.hexSnapFeature = hexSnapFeature
