import { Component, EventEmitter, Input, OnInit, Output } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';

@Component({
  selector: 'app-number-selector',
  templateUrl: './number-selector.component.html',
  styleUrls: ['./number-selector.component.scss']
})
export class NumberSelectorComponent implements OnInit {

  @Output() goBack = new EventEmitter();
  @Output() close = new EventEmitter();
  @Output() next = new EventEmitter();
  @Input() value: number = 1;
  @Input() title: string = "";
  @Input() subtitle?: string;
  @Input() numberInfo?: string;
  @Input() showMoreInfo?: string;
  @Input() maxValue?: number;
  @Input() minValue: number = 0;
  @Input() imgSrc: string = "./assets/images/duplex-house_nobg.png";

  form: FormGroup = new FormGroup({});

  constructor(
    private formBuilder: FormBuilder,
  ) { }

  ngOnInit() {
    this.setForm();
  }

  public setForm() {
    this.form = this.formBuilder.group({
      numMembers: [this.value, Validators.required],
    });
  }

  public back() {
    this.goBack.emit();
  }

  public closeIt() {
    this.close.emit();
  }

  public sumValue() {
    if (this.maxValue) {
      if (this.form.controls['numMembers'].value < this.maxValue) {
        this.form.controls['numMembers'].setValue(this.form.controls['numMembers'].value + 1)
      }
    } else {
      this.form.controls['numMembers'].setValue(this.form.controls['numMembers'].value + 1)
    }
  }

  public lessValue() {
    if (this.form.controls['numMembers'].value > this.minValue) {
      this.form.controls['numMembers'].setValue(this.form.controls['numMembers'].value - 1)
    }
  }

  public goNext() {
    this.next.emit(this.form.controls['numMembers'].value);
  }

}
