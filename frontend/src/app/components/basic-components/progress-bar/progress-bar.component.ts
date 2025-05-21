import { Component, Input } from '@angular/core';

@Component({
  selector: 'progress-bartups',
  templateUrl: './progress-bar.component.html',
  styleUrls: ['./progress-bar.component.scss']
})
export class ProgressBarComponent {

  @Input() stepsNumber?: string;
  @Input() ActualValue: number = 3;
  @Input() maxValue: number = 0;
  @Input() custompercentage?: string;
  @Input() percentage: boolean = true;

  constructor() { }

  getPorcentaje() {
    return `${this.ActualValue * 100 / (this.maxValue !== 0 ? this.maxValue : 1)} %`
  }

}
