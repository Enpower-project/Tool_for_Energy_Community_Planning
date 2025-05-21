import { ViewportScroller } from '@angular/common';
import { Component, EventEmitter, Input, OnInit, Output } from '@angular/core';
import { TranslateService } from '@ngx-translate/core';

@Component({
  selector: 'kpi-cardtups',
  templateUrl: './kpi-card.component.html',
  styleUrls: ['./kpi-card.component.scss']
})
export class KpiCardComponent implements OnInit {

  @Input() disabledCard: boolean = false;
  @Input() title?: string = "";
  @Input() type: string = "";
  @Input() topIcon: string = "";
  @Input() topText: string = "";
  @Input() bodyText: string = "";
  @Input() bodyValue: number = 0;
  @Input() bodyValueText: string = "";
  @Input() footerText: string = "";
  @Input() FooterValueArray?: any[];
  @Input() footerIcon: string = "";
  @Input() openModalKPI: boolean = false;
  @Input() clickable: boolean = true;
  @Input() AboutModalTitle: string = "COMMUNITY.KPI_CARD.ABOUT";
  @Input() kpiObject: any;
  @Output() OnClick = new EventEmitter();

  public footerTextChanging?: string;

  constructor(
    private viewportScroller: ViewportScroller,
    private translate: TranslateService,
  ) { }

  ngOnInit() {
    if (this.FooterValueArray && this.footerText) {
      this.changeFooterValue();
    }
  }

  private changeFooterValue() {
    if (this.FooterValueArray) {
      const index = Math.floor(Math.random() * (this.FooterValueArray?.length ?? 0));
      this.footerTextChanging = this.translate.instant(this.footerText + "." +index).replace("{value}", this.FooterValueArray[index].toFixed(2));
      setTimeout(() => {
        this.changeFooterValue()
      }, 10000);
    }

  }

  public clickOnKPI() {
    if (this.clickable) {
      this.viewportScroller.scrollToPosition([0, 80]);
      this.OnClick.emit();
      this.openModalKPI = !this.openModalKPI;
    }
  }
}
