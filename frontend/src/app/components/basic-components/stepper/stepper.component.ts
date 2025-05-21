import { Component, EventEmitter, Input, OnInit, Output } from '@angular/core';

@Component({
  selector: 'stepper',
  templateUrl: './stepper.component.html',
  styleUrls: ['./stepper.component.scss']
})
export class StepperComponent implements OnInit {

  @Input() numberSteps: number = 4;
  @Input() maxAvailableStep: any = 0;
  @Input() actualStep: number = 0;
  @Input() resetVisibility?: boolean;
  @Input() resetDisabled: boolean | null = false;
  @Output() newStep = new EventEmitter<number>();
  @Output() reset = new EventEmitter<number>();

  constructor() { }

  ngOnInit() {
    if (!this.maxAvailableStep) {
      this.maxAvailableStep = this.numberSteps;
    }
  }

  changeStep(step: number) {
    if (this.maxAvailableStep > step)
      this.newStep.emit(step);
  }

  resetSteps() {
    this.reset.emit();
  }

  getSteps(total: number): number[] {
    return Array(total).fill(0).map((_, index) => index + 1);
  }

}
