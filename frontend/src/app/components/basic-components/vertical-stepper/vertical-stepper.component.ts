import { Component, Input } from '@angular/core';

@Component({
  selector: 'vertical-stepperitups',
  templateUrl: './vertical-stepper.component.html',
  styleUrls: ['./vertical-stepper.component.scss']
})
export class VerticalStepperComponent {

  @Input() steps: any;
  @Input() currentPostion: number = 1;
  constructor() { }
}
