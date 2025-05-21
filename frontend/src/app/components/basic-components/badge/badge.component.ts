import { Component, Input } from '@angular/core';

@Component({
  selector: 'badgitups',
  templateUrl: './badge.component.html',
  styleUrls: ['./badge.component.scss']
})
export class BadgeComponent {

  @Input() title: string = ""
  @Input() disabled: boolean = false;

  constructor() { }

}
