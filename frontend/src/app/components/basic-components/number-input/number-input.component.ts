import { Component, EventEmitter, Input, OnChanges, OnInit, Output, SimpleChanges } from '@angular/core';
import { FormGroup, FormBuilder, Validators } from '@angular/forms';

@Component({
  selector: 'numberitups',
  templateUrl: './number-input.component.html',
  styleUrls: ['./number-input.component.scss']
})
export class NumberInputComponent implements OnInit, OnChanges {

  @Input() initialValue: number = 0;
  @Input() minLimit?: number;
  @Input() maxLimit?: number;
  @Input() numberInfo?: string;
  @Input() showMoreInfo?: string;
  @Input() holdInterval: any;
  @Input() elapsedTime: number = 0;
  @Input() step: number = 1;
  @Output() changeValue = new EventEmitter();

  isCalculating: boolean = false;

  form: FormGroup = new FormGroup({});

  constructor(
    private formBuilder: FormBuilder,
  ) { }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['initialValue'] && this.form.controls['value']) {
      this.form.controls['value'].setValue(this.initialValue ?? 0);
    }
    if (changes['maxLimit'] && this.form.controls['value'] && this.maxLimit) {
      if (this.form.controls['value'].value > this.maxLimit) {
        this.form.controls['value'].setValue(this.maxLimit)
      }
    }
  }

  ngOnInit() {
    this.setForm();
  }

  public setForm() {
    this.form = this.formBuilder.group({
      value: [this.initialValue, Validators.required],
    });
    this.form.controls['value'].valueChanges.subscribe((res) => this.validate(res))
  }

  private validate(num: number) {
    if (num) {
      if (this.maxLimit && num > this.maxLimit) {
        num = this.maxLimit;
        this.form.controls['value'].setValue(num)
      }

      if (this.minLimit && num < this.minLimit) {
        num = this.minLimit;
        this.form.controls['value'].setValue(num)
      }

      this.changeValue.next(num)
    }
  }

  public sumValue() {
    if (this.maxLimit !== undefined) {
      if (this.form.controls['value'].value <= this.maxLimit) {
        this.form.controls['value'].setValue(this.form.controls['value'].value + 1)
      }
    } else {
      this.form.controls['value'].setValue(this.form.controls['value'].value + 1)
    }
  }

  public lessValue() {
    if (this.minLimit !== undefined) {
      if (this.form.controls['value'].value > this.minLimit) {
        this.form.controls['value'].setValue(this.form.controls['value'].value - 1)
      }
    } else {
      this.form.controls['value'].setValue(this.form.controls['value'].value - 1)
    }
  }

  onMouseDown(event: any, plus: boolean) {
    if (event.button === 0 && !this.isCalculating) {
      this.isCalculating = true;
      this.elapsedTime = 0;
      this.step = plus ? 1 : -1;
      this.holdInterval = setInterval(() => {
        this.elapsedTime += 100;
        if (this.elapsedTime > 2000) {
          this.step = plus ? 10 : -10;
        }

        let value = this.form.controls['value'].value + this.step;

        if (this.minLimit !== undefined) {
          if (value < this.minLimit) {
            value = this.form.controls['value'].value;
          }
        }

        if (this.maxLimit !== undefined) {
          if (value > this.maxLimit) {
            value = this.form.controls['value'].value;
          }
        }

        this.form.controls['value'].setValue(value);
      }, 200);
    }

  }

  onMouseUp() {
    clearInterval(this.holdInterval);
    this.isCalculating = false;
  }

  onMouseLeave() {
    clearInterval(this.holdInterval);
    this.isCalculating = false;
  }
}
