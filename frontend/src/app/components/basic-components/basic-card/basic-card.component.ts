import { Component, EventEmitter, Input, Output } from '@angular/core';

@Component({
  selector: 'basic-cardtups',
  templateUrl: './basic-card.component.html',
  styleUrls: ['./basic-card.component.scss']
})
export class BasicCardComponent {

  @Input() cardItem: any;
  @Input() show: boolean = true;
  @Input() selected: boolean = false;
  @Input() iconHoverChange: boolean = true;
  @Output() selectCard = new EventEmitter();
  @Output() showInfo = new EventEmitter()

  constructor() { }

  public selectedACard() {
    this.selectCard.emit(this.cardItem)
  }

  public showInfoCard() {
    this.showInfo.emit()
  }

  public addHover() {
    if (this.iconHoverChange)
      this.cardItem.iconName = this.cardItem.iconName.replace('.svg', '-hover.svg')
  }

  public removeHover() {
    if (this.iconHoverChange)
      this.cardItem.iconName = this.cardItem.iconName.replace('-hover', '')
  }

}
