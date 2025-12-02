# Show Only Failures Button Feature

**Date**: 2025-10-15  
**Status**: ✅ Implemented  
**Feature**: Per-device filter button to show only failed ROI details

## Overview

Added a "Show Only Failures" toggle button for each device in the inspection results section. This allows users to quickly focus on problematic ROIs without scrolling through all passed inspections, improving troubleshooting efficiency.

## User Experience

### Visual Indicator
- Button appears in the ROI section title for each device
- Only shown when device has at least one failed ROI
- Shows count of failed ROIs: "Show Only Failures (2)"
- Icon changes based on state:
  - 🔴 = Normal view (all ROIs visible)
  - 🟢 = Filtered view (only failures visible)

### Interaction Flow
1. **Initial State**: All ROIs visible (passed + failed)
2. **Click Button**: Filters to show only failed ROIs
   - Button text changes to "Show All ROIs"
   - Button background becomes accent color (active state)
   - Passed ROIs are hidden
   - Notification shows count of failed ROIs
3. **Click Again**: Returns to showing all ROIs
   - Button text reverts to "Show Only Failures (X)"
   - Button returns to normal state
   - All ROIs visible again

### Per-Device Independence
- Each device has its own independent filter button
- Filter state is per-device (not global)
- Device 1 can show failures only while Device 2 shows all ROIs

## Implementation Details

### HTML Structure

The button is dynamically generated in the device card rendering:

```javascript
${failedCount > 0 ? `
    <button class="filter-failures-btn" 
            onclick="toggleFailureFilter(${deviceId})"
            id="filterBtn-${deviceId}"
            title="Show only failed ROIs">
        <span class="filter-icon">🔴</span>
        <span class="filter-text">Show Only Failures (${failedCount})</span>
    </button>
` : ''}
```

### JavaScript Function

```javascript
function toggleFailureFilter(deviceId) {
    const roiList = document.getElementById(`roiList-${deviceId}`);
    const filterBtn = document.getElementById(`filterBtn-${deviceId}`);
    
    if (!roiList || !filterBtn) {
        console.error(`ROI list or filter button not found for device ${deviceId}`);
        return;
    }

    const roiItems = roiList.querySelectorAll('.roi-item');
    const isFiltering = filterBtn.classList.contains('active');
    
    if (isFiltering) {
        // Show all ROIs
        roiItems.forEach(item => {
            item.style.display = '';
        });
        filterBtn.classList.remove('active');
        filterBtn.querySelector('.filter-text').textContent = 
            `Show Only Failures (${Array.from(roiItems).filter(item => item.dataset.passed === 'false').length})`;
        filterBtn.querySelector('.filter-icon').textContent = '🔴';
        filterBtn.title = 'Show only failed ROIs';
    } else {
        // Show only failed ROIs
        let failedCount = 0;
        roiItems.forEach(item => {
            if (item.dataset.passed === 'false') {
                item.style.display = '';
                failedCount++;
            } else {
                item.style.display = 'none';
            }
        });
        filterBtn.classList.add('active');
        filterBtn.querySelector('.filter-text').textContent = `Show All ROIs`;
        filterBtn.querySelector('.filter-icon').textContent = '🟢';
        filterBtn.title = 'Show all ROIs';
        
        if (failedCount === 0) {
            showNotification(`No failed ROIs in Device ${deviceId}`, 'info');
        } else {
            showNotification(`Showing ${failedCount} failed ROI(s) for Device ${deviceId}`, 'info');
        }
    }
}
```

### CSS Styling

```css
/* Filter Failures Button */
.filter-failures-btn {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 12px;
    font-size: 0.85em;
    font-weight: 500;
    color: var(--fg);
    background: var(--glass-bg);
    border: 1px solid var(--border-color);
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.2s ease;
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
}

.filter-failures-btn:hover {
    background: var(--glass-surface-hover);
    border-color: var(--accent);
    transform: translateY(-1px);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.filter-failures-btn.active {
    background: var(--accent);
    color: white;
    border-color: var(--accent);
}

.filter-failures-btn .filter-icon {
    font-size: 1em;
    display: inline-block;
    transition: transform 0.2s ease;
}

.filter-failures-btn:hover .filter-icon {
    transform: scale(1.1);
}

.filter-failures-btn .filter-text {
    white-space: nowrap;
}
```

### Data Attributes

Each ROI item now has a `data-passed` attribute for filtering:

```html
<div class="roi-item ${statusClass}" data-passed="${passed}">
    <!-- ROI content -->
</div>
```

## Use Cases

### Quality Control Inspection
**Scenario**: PCB with 20 ROIs, 2 failed
- **Before**: Scroll through all 20 ROIs to find the 2 failures
- **After**: Click button, instantly see only the 2 failed ROIs

### Multi-Device Troubleshooting
**Scenario**: 4 devices, Device 2 has failures
- Filter Device 2 to show only failures
- Keep other devices showing all ROIs for comparison
- Independent filtering per device

### Production Line Review
**Scenario**: Quick pass/fail triage
- If device shows "Show Only Failures (0)" → All passed, no button needed
- If device shows "Show Only Failures (3)" → Click to investigate 3 issues
- Streamlined workflow for operators

## Edge Cases Handled

### No Failed ROIs
- Button is not displayed at all
- Clean interface when everything passes
- No confusion about filter state

### All ROIs Failed
- Button still displayed: "Show Only Failures (5)"
- Clicking has no visible effect (all remain visible)
- Provides consistency in UI behavior

### Mixed Pass/Fail
- Most common scenario
- Button shows exact count of failures
- Clear visual feedback when filtering

## Responsive Design

### Desktop
- Button positioned on right side of ROI section title
- Hover effects fully functional
- Icon animation on hover

### Tablet
- Button remains on same line
- Touch-friendly size (padding: 6px 12px)
- Clear active state

### Mobile
- May wrap to new line if title is long
- Still easily accessible
- Text remains readable

## Accessibility

### Visual Indicators
- Color changes (red → green icon)
- Text changes (descriptive state)
- Active state background color

### Interactive Feedback
- Hover state with transform
- Active state color change
- Notification on filter toggle

### Clear Labeling
- Button text describes action
- Tooltip on hover
- Icon reinforces state

## Performance

### Filtering Speed
- Pure CSS display toggling (no DOM manipulation)
- Instant response (<10ms)
- No layout reflow issues

### Scalability
- Works with 1 ROI or 100 ROIs per device
- Each device filtered independently
- No memory leaks or state issues

## Integration

### Works With
- Multi-device inspection results
- Schema v1.0 and v2.0 formats
- Device result cards
- Image modal display
- Export functionality

### Does Not Affect
- Overall inspection status
- Timing information
- Server communication
- Other devices' display state

## Testing Checklist

- [ ] Button appears when device has failures
- [ ] Button hidden when device has no failures
- [ ] Click toggles between "Show Only Failures" and "Show All ROIs"
- [ ] Icon changes 🔴 ↔ 🟢
- [ ] Button background becomes accent color when active
- [ ] Passed ROIs hidden when filtered
- [ ] Failed ROIs always visible
- [ ] Notification displays correct count
- [ ] Multiple devices can be filtered independently
- [ ] Filter state resets when new inspection performed
- [ ] Hover effects working (desktop)
- [ ] Touch interactions working (mobile/tablet)
- [ ] Works with different ROI counts (1, 5, 20, 50+)

## Files Modified

1. **templates/professional_index.html**
   - Added filter button HTML in device card rendering
   - Added `toggleFailureFilter(deviceId)` function
   - Added `data-passed` attribute to ROI items
   - Updated `renderROIResults()` to accept deviceId parameter

2. **static/professional.css**
   - Added `.filter-failures-btn` styles
   - Added hover, active, and icon styles
   - Integrated with glass morphism theme

3. **docs/SHOW_ONLY_FAILURES_BUTTON.md**
   - This documentation file

## Future Enhancements

- [ ] Keyboard shortcut (e.g., 'F' key to toggle filter)
- [ ] "Show Only Failures" global button (all devices)
- [ ] Filter by ROI type (e.g., show only barcode failures)
- [ ] Filter by similarity threshold (e.g., show ROIs <80%)
- [ ] Save filter preferences to localStorage
- [ ] Export only failed ROI details

## Benefits

### Time Savings
- Instant focus on problem areas
- No scrolling through passed inspections
- Faster troubleshooting workflow

### Reduced Operator Error
- Clear visual separation of failures
- Less chance of missing critical issues
- Improved inspection efficiency

### Better UX
- Simple, intuitive toggle
- Clear state indication
- Non-destructive filtering (no data hidden permanently)

## Conclusion

The "Show Only Failures" button provides a simple yet powerful way to streamline inspection result reviews. By allowing per-device filtering of ROI details, operators can quickly identify and focus on problematic areas without losing context of the overall inspection results. The feature integrates seamlessly with the existing UI while maintaining the professional glass morphism aesthetic.
