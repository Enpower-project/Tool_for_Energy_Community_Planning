import { Component, Input, OnInit } from '@angular/core';

@Component({
  selector: 'horizontal-mentups',
  templateUrl: './horizontal-menu.component.html',
  styleUrls: ['./horizontal-menu.component.scss']
})
export class HorizontalMenuComponent implements OnInit {

  @Input() namesMenu: string[] = []
  @Input() selectedTab: number = 0;
  @Input() beforeTab: number = 0;
  @Input() menuStyle: string = "";
  @Input() clasicStyle: boolean = true;

  constructor() { }

  ngOnInit() {
  }

  public changeSelectedTab(index: number) {
    this.beforeTab = this.selectedTab;
    this.selectedTab = index;

  }

  getWidth() {
    if (this.namesMenu.length > 0)
      return `${100 / this.namesMenu.length}%`;
    else
      return '100%'
  }

}
