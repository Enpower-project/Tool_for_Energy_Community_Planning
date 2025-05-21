import { AfterViewInit, Component, ElementRef, EventEmitter, Input, OnInit, Output } from '@angular/core';
import { EChartsOption } from 'echarts';

@Component({
  selector: 'kpi-modalitups',
  templateUrl: './kpi-modal.component.html',
  styleUrls: ['./kpi-modal.component.scss']
})
export class KpiModalComponent implements OnInit, AfterViewInit {

  @Input() isOpen: boolean = false;
  @Input() title: string = "";
  @Input() badges: string[] = [];
  @Input() energyValue: string = "";
  @Input() energyDescription: string = "";
  @Input() messages: string[] = [];
  @Input() activatedMessage: string = "s";
  @Input() iconMessage: string = "";
  @Input() goalTitle: string = "";
  @Input() goalDescription: string = "";
  @Input() values: any = [];
  @Output() closeModal = new EventEmitter();

  chartOption: EChartsOption = {
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: [],
    },
    yAxis: {
      type: 'value',
    },
    series: [
      {
        data: [],
        type: 'line',
        areaStyle: {}
      },
    ],
  };

  constructor(
    private el: ElementRef
  ) { }

  ngOnInit() {
    this.generateChart()
  }

  ngAfterViewInit(): void {
  }

  private generateChart() {
    if (this.values && this.values.length > 0) {
      const xData = Array.from({ length: this.values.length }, (_, i) => i);

      this.chartOption = {
        xAxis: {
          type: 'category',
          boundaryGap: false,
          data: xData,
          axisLabel: {
            formatter: (value, index) => {
              if (index >= 0 && index < 730) return 'Jan';
              if (index >= 730 && index < 1460) return 'Feb';
              if (index >= 1460 && index < 2190) return 'Mar';
              if (index >= 2190 && index < 2920) return 'Apr';
              if (index >= 2920 && index < 3650) return 'May';
              if (index >= 3650 && index < 4380) return 'Jun';
              if (index >= 4380 && index < 5110) return 'Jul';
              if (index >= 5110 && index < 5840) return 'Aug';
              if (index >= 5840 && index < 6570) return 'Sep';
              if (index >= 6570 && index < 7300) return 'Oct';
              if (index >= 7300 && index < 8030) return 'Nov';
              if (index >= 8030 && index <= 8760) return 'Dec';
              return '';
            },
          },
        },
        yAxis: {
          type: 'value',
        },
        series: [
          {
            data: this.values.map((val: number) => val),
            type: 'line',
            lineStyle: {
              color: '#3B62AB',     
              width: 2
            },
            areaStyle: {
              color: 'rgba(0, 155, 164, 0.75)' 
            },
            itemStyle: {
            color: '#006276'
            }
          },
        ],
      };
    }
  }

  public close() {
    this.closeModal.emit();
  }


}
