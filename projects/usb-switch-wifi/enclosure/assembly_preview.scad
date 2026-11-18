include <usb_switch_enclosure.scad>
PART="none";
EXPLODE=0;
module pcbmodel(){
 color("darkgreen") translate([OX,OY,PCB_Z]) cube([PCB_W,PCB_H,PCB_T]);
 color("silver") translate([sx(8.7)-6.65, sy(0)-14.05, TOP_Z]) cube([13.3,14.05,7.1]);
 color("silver") translate([sx(25.5)-6.65, sy(0)-14.05, TOP_Z]) cube([13.3,14.05,7.1]);
 color("silver") translate([sx(42.3)-6.65, sy(0)-14.05, TOP_Z]) cube([13.3,14.05,7.1]);
 color("silver") translate([sx(59.1)-6.65, sy(0)-14.05, TOP_Z]) cube([13.3,14.05,7.1]);
 color("silver") translate([sx(8.7)-6.65, sy(53.2), TOP_Z]) cube([13.3,14.05,7.1]);
 color("silver") translate([sx(25.5)-6.65, sy(53.2), TOP_Z]) cube([13.3,14.05,7.1]);
 color("white") translate([sx(4.4+3.81)-5.1, sy(16.3+8.89)-10.1, TOP_Z]) cube([10.2,20.2,12.0]);
 color("white") translate([sx(16.399999+3.81)-5.1, sy(16.3+8.89)-10.1, TOP_Z]) cube([10.2,20.2,12.0]);
 color("royalblue") translate([sx(43.269999-1.37), sy(27.21+25.99), TOP_Z+2.5]) cube([25.6,34.2,1.0]);
 color("gray") translate([sx(43.269999+3.9), sy(27.21+15), TOP_Z+3.5]) cube([15,15,3]);
 color("silver") translate([sx(43.269999+11.43)-4, sy(27.21+25.99)-0.6, TOP_Z+3.5]) cube([8,5.6,2.8]);
 color("black") translate([sx(29.6),sy(26.5),TOP_Z]) cylinder(d=6.3,h=5.4);
}
base(); pcbmodel(); translate([0,0,BASE_H+EXPLODE]) color("lightskyblue",0.55) lid();
