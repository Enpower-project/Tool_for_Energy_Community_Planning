import { Component, EventEmitter, Input, OnInit, Output } from '@angular/core';

@Component({
  selector: 'app-steps-structure',
  templateUrl: './steps-structure.component.html',
  styleUrls: ['./steps-structure.component.scss']
})
export class StepsStructureComponent implements OnInit {

  @Input() disabledButton: boolean = true;
  @Input() title: string = '';
  @Input() subtitle?: string;
  @Input() nextButton: boolean = true;
  @Input() header: boolean = true;
  @Input() loading?: boolean;
  @Output() back = new EventEmitter();
  @Output() close = new EventEmitter();
  @Output() next = new EventEmitter();

  constructor() { }

  ngOnInit() {
  }

  public goBack() {
    this.back.emit()
  }

  public closeIt() {
    this.close.emit()
  }

  public goNext() {
    this.next.emit();
  }

}
