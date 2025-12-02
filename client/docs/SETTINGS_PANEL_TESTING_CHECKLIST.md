# Settings Panel Testing Checklist

## Pre-Testing Setup

- [ ] Flask server running on port 5100
- [ ] Server accessible at http://10.100.27.156:5000
- [ ] Chromium browser open
- [ ] Developer console open (F12) for debugging

## Visual Testing

### Initial Load
- [ ] Settings panel is collapsed on page load
- [ ] Only settings header visible (⚙️ "Setup Configuration" (Not configured) 📂)
- [ ] Inspection button prominently visible
- [ ] No extra scrolling required to see inspection button
- [ ] Status shows "(Not configured)" in gray

### Header Interaction
- [ ] Cog icon (⚙️) rotates 45° on hover
- [ ] Header background lightens on hover
- [ ] Clicking header expands panel smoothly
- [ ] Button icon changes from 📂 to 📁
- [ ] Grid with 4 sections appears

### Collapse/Expand Animation
- [ ] Smooth 0.4s animation
- [ ] Content fades in/out with opacity transition
- [ ] No visual glitches or jumps
- [ ] Backdrop filter effects working

## Functional Testing

### Panel Toggle
- [ ] Click header to expand → panel expands
- [ ] Click header again → panel collapses
- [ ] Button icon updates correctly
- [ ] State persists after page reload

### Status Updates - Server Connection
- [ ] Enter server URL: http://10.100.27.156:5000
- [ ] Click "Connect" button
- [ ] Wait for connection success
- [ ] Status updates to "(Server ✓)" in amber
- [ ] Color changes from gray to amber

### Status Updates - Camera Initialization
- [ ] Select a product from dropdown
- [ ] Select camera from dropdown
- [ ] Click "Initialize with Product" button
- [ ] Wait for initialization success
- [ ] Status updates to "(Server ✓, Product ✓, Camera ✓)" in amber

### Status Updates - Session Creation
- [ ] Click "Create Session" button
- [ ] Wait for session creation success
- [ ] Status updates to "(All configured ✓)" in green
- [ ] Color changes from amber to green

### Status Updates - Session Cleared
- [ ] Click "Close Session" button
- [ ] Status updates to "(Server ✓, Product ✓, Camera ✓)" in amber
- [ ] Green color changes back to amber

### Individual Section Collapse
- [ ] Expand settings panel
- [ ] Each of 4 sections has its own collapse button
- [ ] Individual sections collapse/expand independently
- [ ] Settings panel collapse works with sections collapsed inside

## Responsive Testing

### Desktop (1920x1080)
- [ ] 2x2 grid layout displayed
- [ ] Settings panel full width
- [ ] Hover effects working
- [ ] Inspection button clearly visible

### Tablet (768x1024)
- [ ] 2x2 grid maintained
- [ ] Touch interactions working
- [ ] Panel collapse/expand smooth

### Mobile (375x667)
- [ ] Single column layout
- [ ] Touch interactions working
- [ ] Text readable
- [ ] No horizontal scrolling

## State Persistence

### localStorage Testing
- [ ] Collapse settings panel
- [ ] Refresh page (Ctrl+R)
- [ ] Settings panel still collapsed
- [ ] Expand settings panel
- [ ] Refresh page
- [ ] Settings panel still expanded

### Setup State Persistence
- [ ] Complete full setup (all 4 steps)
- [ ] Status shows "(All configured ✓)"
- [ ] Refresh page
- [ ] Status still shows correct state
- [ ] (Note: Server connection may be lost, but other states should persist)

## Integration Testing

### With Compact UI
- [ ] Individual sections auto-collapse on page load
- [ ] 2x2 grid layout working
- [ ] Spacing consistent
- [ ] Glass effects applied

### With Chromium Optimizations
- [ ] Hardware acceleration active
- [ ] Backdrop filters rendering
- [ ] Animations smooth (60fps)
- [ ] No performance issues

### With Inspection Workflow
- [ ] Complete setup
- [ ] Collapse settings panel
- [ ] Perform inspection
- [ ] Results display correctly
- [ ] Settings panel doesn't interfere

## Console Testing

### JavaScript Errors
- [ ] No errors on page load
- [ ] No errors when toggling panel
- [ ] No errors during setup workflow
- [ ] updateSetupStatus() called at correct times

### Network Requests
- [ ] Server connection successful
- [ ] Camera initialization successful
- [ ] Session creation successful
- [ ] No failed API calls

## Edge Cases

### Empty States
- [ ] Panel works with no server connection
- [ ] Panel works with no product selected
- [ ] Panel works with no camera
- [ ] Panel works with no session

### Rapid Clicks
- [ ] Click header rapidly multiple times
- [ ] Animation doesn't break
- [ ] State remains consistent
- [ ] No visual glitches

### Browser Refresh
- [ ] Refresh during panel animation
- [ ] State recovers correctly
- [ ] No orphaned localStorage values
- [ ] No broken UI elements

## Accessibility

### Keyboard Navigation
- [ ] Tab through settings header
- [ ] Enter/Space toggles panel
- [ ] Focus visible on interactive elements
- [ ] Tab order logical

### Screen Reader (Optional)
- [ ] Settings header announced
- [ ] Status changes announced
- [ ] Button state changes announced

## Browser Compatibility

### Chromium (Primary)
- [ ] All features working
- [ ] Backdrop filters rendering
- [ ] Animations smooth
- [ ] No console errors

### Firefox (Secondary)
- [ ] Panel toggle working
- [ ] Status updates working
- [ ] Animations working (may need fallback for backdrop-filter)

## Performance

### Load Time
- [ ] Page loads in <2 seconds
- [ ] No blocking on settings panel JS
- [ ] CSS loads without flash

### Runtime
- [ ] Panel toggle <400ms
- [ ] No lag when expanding/collapsing
- [ ] Status updates <100ms
- [ ] Smooth animations throughout

## Bug Reports

### Issues Found
- [ ] Issue 1: _________________________
- [ ] Issue 2: _________________________
- [ ] Issue 3: _________________________

## Sign-Off

- [ ] All visual tests passed
- [ ] All functional tests passed
- [ ] All integration tests passed
- [ ] No critical bugs found
- [ ] Ready for production use

**Tester Name**: ___________________  
**Date**: ___________________  
**Browser Version**: Chromium ___________________  
**Screen Resolution**: ___________________

## Notes

_Add any additional observations or issues here:_

---

## Quick Test Commands

```bash
# Start Flask server
cd /home/pi/visual-aoi-client
python3 app.py

# Open in Chromium (from terminal)
chromium-browser http://localhost:5100

# Check JavaScript console for errors
# Press F12 in browser, select Console tab

# Test localStorage
# In browser console:
localStorage.getItem('aoi-settings-collapsed')
localStorage.getItem('aoi-collapsed-sections')
```

## Expected Console Logs

When toggling panel:
```
Settings panel expanded
Settings panel collapsed
```

When updating status:
```
Setup status updated: (Not configured)
Setup status updated: (Server ✓)
Setup status updated: (Server ✓, Product ✓, Camera ✓)
Setup status updated: (All configured ✓)
```

## CSS Verification

Check in DevTools that these styles are applied:

**Panel collapsed:**
```css
.settings-content {
  max-height: 0px;
  opacity: 0;
}
.settings-panel.collapsed {
  margin-bottom: 12px;
}
```

**Panel expanded:**
```css
.settings-content {
  max-height: [calculated]px;
  opacity: 1;
}
```
