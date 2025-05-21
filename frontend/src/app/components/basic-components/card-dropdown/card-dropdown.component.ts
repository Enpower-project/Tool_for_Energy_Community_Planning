import { Component, Input } from '@angular/core';

@Component({
  selector: 'card-droptups',
  templateUrl: './card-dropdown.component.html',
  styleUrls: ['./card-dropdown.component.scss']
})
export class CardDropdownComponent {

  @Input() openCardScenario: boolean = false;
  @Input() description?: string = "";
  @Input() title: string = "";
  @Input() icon: string = "";
  @Input() score?: number = undefined;
  @Input() scoreSTR?: string;
  @Input() votes?: number;
  @Input() info?: any = null;

  constructor() { }

}
