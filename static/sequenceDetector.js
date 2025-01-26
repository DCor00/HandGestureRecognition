// sequenceDetector.js
export class SequenceDetector {
    constructor(sequence, historySize = 30) {
        this.sequence = sequence;
        this.historySize = historySize;
        this.gestureHistory = [];
        this.onSequenceDetected = null; // Callback function
    }

    addGesture(gesture) {
        this.gestureHistory.push(gesture);
        if (this.gestureHistory.length > this.historySize) {
            this.gestureHistory.shift();
        }
        
        if (this.checkSequence() && this.onSequenceDetected) {
            this.onSequenceDetected();
        }
    }

    checkSequence() {
        if (this.gestureHistory.length < this.sequence.length) return false;
        return this.sequence.every((g, i) => 
            g === this.gestureHistory[this.gestureHistory.length - this.sequence.length + i]
        );
    }

    reset() {
        this.gestureHistory = [];
    }
}