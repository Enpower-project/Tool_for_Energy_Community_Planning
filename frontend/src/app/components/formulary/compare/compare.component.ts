import { Component, ElementRef, EventEmitter, Input, OnChanges, OnInit, Output, SimpleChanges } from '@angular/core';
import { TranslateService } from '@ngx-translate/core';
import { EChartsOption } from 'echarts';
import { CardInfo } from '../../../data/types';
import { GeneralService } from '../../../services/general.service';

@Component({
  selector: 'app-compare',
  templateUrl: './compare.component.html',
  styleUrls: ['./compare.component.scss']
})
export class CompareComponent implements OnInit, OnChanges {

  @Input() isOpen: boolean = false;
  @Input() isLoading: boolean = true;
  @Input() title: string = "COMMUNITY.COMPARE.COMPARE";
  @Input() description: string = "COMMUNITY.COMPARE.DESCRIPTION";
  @Input() selectTitle: string = "COMMUNITY.COMPARE.SELECT_ALTERNATIVE";
  @Input() selectResult: string = "COMMUNITY.COMPARE.SELECT_RESULT";
  @Input() selectOptions: string[] = [];
  @Input() options: any = [];
  @Input() selectTypes: string[] = [];
  @Input() types: any = [
    {
      id: "total_primary_energy_[kWh]",
      name: "total_primary_energy_[kWh]",
      title: "COMMUNITY.KPI_CARD.ENERGY_USE.KPI_NAME",
      icon: "./assets/icons/ray_icon_pink.svg",
    },
    {
      id: "households_costs_[€]",
      name: "households_costs_[€]",
      title: "COMMUNITY.KPI_CARD.PRODUCTION_COSTS.KPI_NAME",
      icon: "./assets/icons/coins-blue.svg",
    },
    {
      id: "Total_co2",
      name: "Total_co2",
      title: "COMMUNITY.KPI_CARD.CO2_EMISSIONS_REDUCTION.KPI_NAME",
      icon: "./assets/icons/cloud-green.svg",
    },
    {
      id: "BatteryUsageEstimation_[charges]",
      name: "BatteryUsageEstimation_[charges]",
      title: "title",
      icon: "",
    },
    {
      id: "CarbonEmissionsPerKilometer_[km]",
      name: "CarbonEmissionsPerKilometer_[km]",
      title: "title",
      icon: "",
    },
    {
      id: "ElectricCarChargingEstimation_[charges]",
      name: "ElectricCarChargingEstimation_[charges]",
      title: "title",
      icon: "",
    },
    {
      id: "EquivalentTVHours_[h]",
      name: "EquivalentTVHours_[h]",
      title: "title",
      icon: "",
    },
    {
      id: "EquivalentstreamingHours_[h]",
      name: "EquivalentstreamingHours_[h]",
      title: "title",
      icon: "",
    },
    {
      id: "streamingEmissionsImpact_[hours]",
      name: "streamingEmissionsImpact_[hours]",
      title: "title",
      icon: "",
    },
    {
      id: "renewable_primary_energy_[kWh]",
      name: "renewable_primary_energy_[kWh]",
      title: "title",
      icon: "",
    },
    {
      id: "non_renewable_primary_energy_[kWh]",
      name: "non_renewable_primary_energy_[kWh]",
      title: "title",
      icon: "",
    },
  ];
  @Input() selectCaption: string = "";
  @Input() timeMenu: string[] = ["TIME.YEARLY", "TIME.MONTHLY"];
  @Input() goalTitle: string = "";
  @Input() goalDescription: string = "";
  @Input() kpiObject: any;
  @Input() optionIndex: number = 0;
  @Input() kpisData?: any

  @Output() closeModal = new EventEmitter();
  @Output() changeAlternative = new EventEmitter();

  @Input() chartOption: EChartsOption[] = [];

  public type: any = this.types[0];

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['options']) {
      this.selectOptions = this.options.map((option: any) => option?.title);
    }
    if (changes['types']) {
      this.selectTypes = this.types.map((type: any) => type.title);
    }

    if (changes['isLoading']) {
      if (this.isLoading == false) {
        this.realoadChart();
      }
    }

    if (changes['kpiObject']) {
      if (this.kpiObject[this.options[0]?.title]) {
        this.realoadChart();
      }
    }

  }

  constructor(
    private el: ElementRef,
    private translate: TranslateService,
    private generalService: GeneralService
  ) { }

  ngOnInit() {

    if (this.options.length > 0) {
      this.changeAlternative.emit(this.options[this.optionIndex]?.id);

      this.selectTypes = this.types.map((type: any) => type.title);

      if (this.kpisData) {
        this.goalDescription = this.kpisData[0]?.card
      }
    }
  }

  public close() {
    this.closeModal.emit();
  }

  public selectOption(index: number) {
    this.optionIndex = index;
    this.changeAlternative.emit(this.options[index]?.id);
  }

  public changeType(index: number) {
    this.type = this.types[index];
    this.goalDescription = this.kpisData[index]?.card ?? "text"
    this.realoadChart()
  }

  private realoadChart() {
    this.getGraphArray();
  }

  private getGraphArray() {
    let unit = this.kpiObject.context[this.type.id].unit ?? '';
    let alternativeValue = 0;
    let alternativeArray = [0];
    if (this.kpiObject[this.options[this.optionIndex]?.title]) {
      alternativeArray = this.generalService.agruparArrayPorAño(this.kpiObject[this.options[this.optionIndex]?.title][this.type.id].value)
      alternativeValue = this.generalService.sum(this.kpiObject[this.options[this.optionIndex]?.title][this.type.id].value);
    }

    this.chartOption = [
      {
        color: ['#3B62AB', '#4CB689'],
        tooltip: {
          trigger: 'item',
          formatter: '{a} <br/>{b}: {c} ' + unit,
        },
        legend: {
          data: ['Current community', this.options[this.optionIndex]?.title ?? 'Alternative'],
        },
        xAxis: {
          type: 'category',
          data: [],
        },
        yAxis: {
          type: 'value',
        },
        series: [
          {
            name: 'Current community',
            type: 'bar',
            data: [this.generalService.round2Decimals(this.generalService.sum(this.kpiObject.context[this.type.id].value))],
            barWidth: '30%',
          },
          {
            name: this.options[this.optionIndex]?.title ?? 'Alternative',
            type: 'bar',
            data: [this.generalService.round2Decimals(alternativeValue)],
            barWidth: '30%',
          },
        ],
      },
      {
        color: ['#3B62AB', '#4CB689'],
        tooltip: {
          trigger: 'item',
          formatter: '{a} <br/>{b}: {c} ' + unit,
        },
        legend: {
          data: ['Current community', this.options[this.optionIndex]?.title ?? 'Alternative'],
          top: '10%',
        },
        xAxis: {
          type: 'category',
          data: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
          axisLabel: {
            rotate: 45,
          },
        },
        yAxis: {
          type: 'value',
        },
        series: [
          {
            name: 'Current community',
            type: 'bar',
            data: this.generalService.agruparArrayPorAño(this.kpiObject.context[this.type.id].value),
            barWidth: '40%',
          },
          {
            name: this.options[this.optionIndex]?.title ?? 'Alternative',
            type: 'bar',
            data: alternativeArray,
            barWidth: '40%',
          },
        ],
      }
    ] as any;

  }
}
