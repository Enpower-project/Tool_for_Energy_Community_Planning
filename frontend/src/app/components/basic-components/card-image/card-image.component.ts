import { Component, EventEmitter, Input, OnInit, Output } from '@angular/core';

@Component({
  selector: 'card-imaginitups',
  templateUrl: './card-image.component.html',
  styleUrls: ['./card-image.component.scss']
})
export class CardImageComponent implements OnInit {

  @Input() imgUrl?:string;
  @Input() titleCard: string = "";
  @Input() descriptionCard: string = "";
  @Input() flagUrl?: string;
  @Input() readmore: boolean = false;
  @Input() showMore: boolean = false;
  @Input() badges?: string[];
  @Output() imageClick = new EventEmitter();

  constructor() { }

  ngOnInit() {
  }

  public clickOnImage() {
    this.imageClick.emit()
  }

}
