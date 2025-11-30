// Test the emergency button functionality
console.log("Testing emergency button functionality...");

// Simulate clicking the emergency button
const emergencyBtn = document.getElementById('emergency-button');
if (emergencyBtn) {
    console.log("Emergency button found, simulating click...");
    emergencyBtn.click();
} else {
    console.log("Emergency button not found");
}