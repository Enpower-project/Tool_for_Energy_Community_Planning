import { Component, Input, OnInit } from '@angular/core';

@Component({
  selector: 'dropdowntups',
  templateUrl: './dropdown.component.html',
  styleUrls: ['./dropdown.component.scss']
})
export class DropdownComponent implements OnInit {

  @Input() title:string = "";
  @Input() mainText:string = "";
  @Input() subText:string = "";
  @Input() active: boolean = false;
  @Input() showMore: boolean = false;
  @Input() smartDropdown:boolean = false;

  constructor() { }

  ngOnInit() {
  }

}
