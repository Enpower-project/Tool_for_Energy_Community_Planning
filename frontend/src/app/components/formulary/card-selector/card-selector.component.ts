import { Component, EventEmitter, Input, OnInit, Output } from '@angular/core';
import { FormGroup, FormBuilder, Validators } from '@angular/forms';
import { CardInfo, cardArrayModule } from '../../../data/types';

@Component({
  selector: 'app-card-selector',
  templateUrl: './card-selector.component.html',
  styleUrls: ['./card-selector.component.scss']
})
export class CardSelectorComponent implements OnInit {

  @Input() selectedcard?: number;
  @Input() initialLimit: number = 3;
  @Input() limit: number = this.initialLimit;
  @Input() loading: boolean = false;
  @Output() goBack = new EventEmitter();
  @Output() close = new EventEmitter();
  @Output() next = new EventEmitter();

  form: FormGroup = new FormGroup({});
  cardArray: CardInfo[] = cardArrayModule;
  textShowMore: string = 'SEE_MORE'

  constructor(
    private formBuilder: FormBuilder,
  ) { }

  ngOnInit() {
    this.setForm();
  }

  public setForm() {
    this.form = this.formBuilder.group({
      card: [this.selectedcard, Validators.required],
    });
  }

  public back() {
    this.goBack.emit();
  }

  public closeIt() {
    this.close.emit();
  }

  public goNext() {
    const cardObject= {
      position: this.selectedcard,
      card: this.cardArray[this.selectedcard ?? 0]
    }
    this.next.emit(cardObject);
  }

  showMoreOrLess() {
    this.limit = this.limit === this.initialLimit ? this.cardArray.length : this.initialLimit;
    this.textShowMore = this.limit === this.initialLimit ? 'SEE_MORE' : 'SEE_LESS';
  }

  public showInfo(cardItem: any) {
  }

  public selectCard(cardItem: any, position: number) {
    this.selectedcard = position;
    this.form.controls["card"].setValue(this.selectedcard);
  }
}
