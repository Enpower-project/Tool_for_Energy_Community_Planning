import { Component, OnInit } from '@angular/core';
import { FormGroup, FormBuilder, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { TranslateService } from '@ngx-translate/core';
import { APP_ROUTES } from '../../data/routes';

@Component({
  selector: 'app-faq',
  templateUrl: './faq.component.html',
  styleUrls: ['./faq.component.scss']
})
export class FaqComponent implements OnInit {

  public APP_ROUTES = APP_ROUTES;
  public showBurgerMenu:boolean = false;
  public langs = [
    {
      name: "LANGUAGE_MENU.ENGLISH",
      value: "en"
    },
    {
      name: "LANGUAGE_MENU.SPANISH",
      value: "es"
    },
    {
      name: "LANGUAGE_MENU.GERMAN",
      value: "en"
    },
    {
      name: "LANGUAGE_MENU.ITALIAN",
      value: "en"
    },
    {
      name: "LANGUAGE_MENU.SWEDISH",
      value: "en"
    },
    {
      name: "LANGUAGE_MENU.BASQUE",
      value: "en"
    },

  ]


  form: FormGroup = new FormGroup({});
  constructor(
    private router: Router,
    private formBuilder: FormBuilder,
    private translate: TranslateService
  ) { }

  ngOnInit() {
    this.setForm();
  }

  public setForm() {
    this.form = this.formBuilder.group({
      lang: [this.translate.currentLang, Validators.required],
    });
    this.form.controls['lang'].valueChanges.subscribe(() => { this.changeLang() })
  }

  goTo(route:string) {
    this.router.navigate(['/' + route])
}
  open() {

  }

  changeLang() {
    this.translate.use(this.form.controls['lang'].value);
  }

}
