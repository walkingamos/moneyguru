/* 
Copyright 2011 Hardcoded Software (http://www.hardcoded.net)

This software is licensed under the "BSD" License as described in the "LICENSE" file, 
which should be included with this package. The terms are also available at 
http://www.hardcoded.net/licenses/bsd_license
*/

#import <Cocoa/Cocoa.h>
#import "HSGUIController2.h"
#import "MGChartView.h"
#import "PyChart.h"

@interface MGChart : HSGUIController2 {}
- (id)initWithPy:(id)aPy;
- (MGChartView *)view;
- (PyChart *)model;

/* Python callbacks */
- (void)refresh;
@end
