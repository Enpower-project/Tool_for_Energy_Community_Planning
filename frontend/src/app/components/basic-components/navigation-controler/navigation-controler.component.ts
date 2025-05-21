import { Component, EventEmitter, Input, OnChanges, OnInit, Output, SimpleChanges } from '@angular/core';
import { NavigationControl } from '../../../data/types';

@Component({
  selector: 'nav-controlitups',
  templateUrl: './navigation-controler.component.html',
  styleUrls: ['./navigation-controler.component.scss']
})
export class NavigationControlerComponent implements OnInit, OnChanges {

  @Input() navigation: NavigationControl = {} as NavigationControl
  @Input() currentStep: number = 0;
  @Output() navigate = new EventEmitter();
  public icon = this.navigation.icon;

  constructor() { }

  ngOnInit() {
    this.icon = this.navigation.icon;
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['navigation']) {
      this.icon = this.navigation.icon;
    }
  }

  public clickToNavigate(item: any) {
    this.navigate.next({
      url: item.url,
      urlType: item.urlType,
      item: item
    });
  }
}
