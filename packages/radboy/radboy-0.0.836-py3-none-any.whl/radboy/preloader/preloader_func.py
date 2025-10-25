from radboy.DB.db import *
from radboy.DB.RandomStringUtil import *
import radboy.Unified.Unified as unified
import radboy.possibleCode as pc
from radboy.DB.Prompt import *
from radboy.DB.Prompt import prefix_text
from radboy.TasksMode.ReFormula import *
from radboy.TasksMode.SetEntryNEU import *
from radboy.FB.FormBuilder import *
from radboy.FB.FBMTXT import *
from radboy.RNE.RNE import *
from radboy.Lookup2.Lookup2 import Lookup as Lookup2
from radboy.DayLog.DayLogger import *
from radboy.DB.masterLookup import *
from collections import namedtuple,OrderedDict
import nanoid,qrcode,io
from password_generator import PasswordGenerator
import random
from pint import UnitRegistry
import pandas as pd
import numpy as np
from datetime import *
from colored import Style,Fore
import json,sys,math,re,calendar,hashlib,haversine
from time import sleep
import itertools
import decimal
from decimal import localcontext,Decimal
unit_registry=pint.UnitRegistry()
import math,scipy
from radboy.HowDoYouDefineMe.CoreEmotions import *


def volume():
    with localcontext() as ctx:
        ctx.prec=int(db.detectGetOrSet("lsbld ROUNDTO default",4,setValue=False,literal=True))
        #print(f"{Fore.light_green}Precision {ctx.prec}{Fore.light_yellow}")
        height=Prompt.__init2__(None,func=FormBuilderMkText,ptext=f"{Fore.light_green}Precision {ctx.prec}{Fore.light_yellow} height?: ",helpText="height=1",data="dec.dec")
        if height is None:
            return
        elif height in ['d',]:
            height=Decimal('1')
        
        width=Prompt.__init2__(None,func=FormBuilderMkText,ptext=f"{Fore.light_green}Precision {ctx.prec}{Fore.light_yellow} width?: ",helpText="width=1 ",data="dec.dec")
        if width is None:
            return
        elif width in ['d',]:
            width=Decimal('1')
    


        length=Prompt.__init2__(None,func=FormBuilderMkText,ptext=f"{Fore.light_green}Precision {ctx.prec}{Fore.light_yellow} length?: ",helpText="length=1",data="dec.dec")
        if length is None:
            return
        elif length in ['d',]:
            length=Decimal('1')

        return length*width*height

def volume_pint():
    with localcontext() as ctx:
        ctx.prec=int(db.detectGetOrSet("lsbld ROUNDTO default",4,setValue=False,literal=True))
        height=Prompt.__init2__(None,func=FormBuilderMkText,ptext=f"{Fore.light_green}Precision {ctx.prec}{Fore.light_yellow} height?: ",helpText="height=1",data="string")
        if height is None:
            return
        elif height in ['d',]:
            height='1'
        
        width=Prompt.__init2__(None,func=FormBuilderMkText,ptext=f"{Fore.light_green}Precision {ctx.prec}{Fore.light_yellow} width?: ",helpText="width=1 ",data="string")
        if width is None:
            return
        elif width in ['d',]:
            width='1'
        


        length=Prompt.__init2__(None,func=FormBuilderMkText,ptext=f"{Fore.light_green}Precision {ctx.prec}{Fore.light_yellow} length?: ",helpText="length=1",data="string")
        if length is None:
            return
        elif length in ['d',]:
            length='1'

        return unit_registry.Quantity(length)*unit_registry.Quantity(width)*unit_registry.Quantity(height)

def inductance_pint():
    with localcontext() as ctx:
        ctx.prec=int(db.detectGetOrSet("lsbld ROUNDTO default",4,setValue=False,literal=True))
        relative_permeability=Prompt.__init2__(None,func=FormBuilderMkText,ptext=f"{Fore.light_green}Precision {ctx.prec}{Fore.light_yellow} relative_permeability?: ",helpText="relative_permeability(air)=1",data="string")
        if relative_permeability is None:
            return
        elif relative_permeability in ['d',]:
            relative_permeability='1'
        relative_permeability=float(relative_permeability)

        turns_of_wire_on_coil=Prompt.__init2__(None,func=FormBuilderMkText,ptext=f"{Fore.light_green}Precision {ctx.prec}{Fore.light_yellow} turns_of_wire_on_coil?: ",helpText="turns_of_wire_on_coil=1",data="string")
        if turns_of_wire_on_coil is None:
            return
        elif turns_of_wire_on_coil in ['d',]:
            turns_of_wire_on_coil='1'
        turns_of_wire_on_coil=int(turns_of_wire_on_coil)

        #convert to meters
        core_cross_sectional_area_meters=Prompt.__init2__(None,func=FormBuilderMkText,ptext=f"{Fore.light_green}Precision {ctx.prec}{Fore.light_yellow} core_cross_sectional_area_meters?: ",helpText="core_cross_sectional_area_meters=1",data="string")
        if core_cross_sectional_area_meters is None:
            return
        elif core_cross_sectional_area_meters in ['d',]:
            core_cross_sectional_area_meters='1m'
        try:
            core_cross_sectional_area_meters=unit_registry.Quantity(core_cross_sectional_area_meters).to("meters")
        except Exception as e:
            print(e,"defaulting to meters")
            core_cross_sectional_area_meters=unit_registry.Quantity(f"{core_cross_sectional_area_meters} meters")

        length_of_coil_meters=Prompt.__init2__(None,func=FormBuilderMkText,ptext=f"{Fore.light_green}Precision {ctx.prec}{Fore.light_yellow} length_of_coil_meters?: ",helpText="length_of_coil_meters=1",data="string")
        if length_of_coil_meters is None:
            return
        elif length_of_coil_meters in ['d',]:
            length_of_coil_meters='1m'
        try:
            length_of_coil_meters=unit_registry.Quantity(length_of_coil_meters).to('meters')
        except Exception as e:
            print(e,"defaulting to meters")
            length_of_coil_meters=unit_registry.Quantity(f"{length_of_coil_meters} meters")
        
        numerator=((turns_of_wire_on_coil**2)*core_cross_sectional_area_meters)
        f=relative_permeability*(numerator/length_of_coil_meters)*1.26e-6
        f=unit_registry.Quantity(f"{f.magnitude} H")
        return f

def resonant_inductance():
    with localcontext() as ctx:
        ctx.prec=int(db.detectGetOrSet("lsbld ROUNDTO default",4,setValue=False,literal=True))
        hertz=1e9
        while True:
            try:
                hertz=Control(func=FormBuilderMkText,ptext=f"{Fore.light_green}Precision {ctx.prec}{Fore.light_yellow} frequency in hertz[530 kilohertz]? ",helpText="frequency in hertz",data="string")
                if hertz is None:
                    return
                elif hertz in ['d','']:
                    hertz="530 megahertz"
                print(hertz)
                x=unit_registry.Quantity(hertz)
                if x:
                    hertz=x.to("hertz")
                else:
                    hertz=1e6
                break
            except Exception as e:
                print(e)

        
        while True:
            try:
                capacitance=Control(func=FormBuilderMkText,ptext=f"{Fore.light_green}Precision {ctx.prec}{Fore.light_yellow} capacitance[365 picofarads]? ",helpText="capacitance in farads",data="string")
                if capacitance is None:
                    return
                elif capacitance in ['d',]:
                    capacitance="365 picofarads"
                x=unit_registry.Quantity(capacitance)
                if x:
                    x=x.to("farads")
                farads=x.magnitude
                break
            except Exception as e:
                print(e)

        inductance=1/(decc(4*math.pi**2)*decc(hertz.magnitude**2,cf=13)*decc(farads,cf=13))

        L=unit_registry.Quantity(inductance,"henry")
        return L

def air_coil_cap():
    with localcontext() as ctx:
        ctx.prec=int(db.detectGetOrSet("lsbld ROUNDTO default",4,setValue=False,literal=True))
        '''C = 1 / (4π²f²L)'''
        while True:
            try:
                frequency=Control(func=FormBuilderMkText,ptext=f"{Fore.light_green}Precision {ctx.prec}{Fore.light_yellow} frequency? ",helpText="frequency",data="string")
                if frequency is None:
                    return
                elif frequency in ['d',]:
                    frequency="1410 kilohertz"
                x=unit_registry.Quantity(frequency)
                if x:
                    x=x.to("hertz")
                frequency=decc(x.magnitude**2)
                break
            except Exception as e:
                print(e)
        
        while True:
            try:
                inductance=Control(func=FormBuilderMkText,ptext=f"{Fore.light_green}Precision {ctx.prec}{Fore.light_yellow} inductance(356 microhenry): ",helpText="coil inductance",data="string")
                if inductance is None:
                    return
                elif inductance in ['d',]:
                    inductance="356 microhenry"
                x=unit_registry.Quantity(inductance)
                if x:
                    x=x.to("henry")
                inductance=decc(x.magnitude,cf=20)
                break
            except Exception as e:
                print(e)
        

        
        farads=1/(inductance*frequency*decc(4*math.pi**2))
        return unit_registry.Quantity(farads,"farad")

def air_coil():
    with localcontext() as ctx:
        ctx.prec=int(db.detectGetOrSet("lsbld ROUNDTO default",4,setValue=False,literal=True))
        '''
        The formula for inductance - using toilet rolls, PVC pipe etc. can be well approximated by:


                          0.394 * r2 * N2
        Inductance L = ________________
                         ( 9 *r ) + ( 10 * Len)
        Here:
        N = number of turns
        r = radius of the coil i.e. form diameter (in cm.) divided by 2
        Len = length of the coil - again in cm.
        L = inductance in uH.
        * = multiply by
        '''
        while True:
            try:
                diameter=Control(func=FormBuilderMkText,ptext=f"{Fore.light_green}Precision {ctx.prec}{Fore.light_yellow} diameter in cm [2 cm]? ",helpText="diamater of coil",data="string")
                if diameter is None:
                    return
                elif diameter in ['d',]:
                    diameter="2 cm"
                x=unit_registry.Quantity(diameter)
                if x:
                    x=x.to("centimeter")
                diameter=x.magnitude
                break
            except Exception as e:
                print(e)
        radius=decc(diameter/2)
        while True:
            try:
                length=Control(func=FormBuilderMkText,ptext=f"{Fore.light_green}Precision {ctx.prec}{Fore.light_yellow} length in cm [2 cm]? ",helpText="length of coil",data="string")
                if length is None:
                    return
                elif length in ['d',]:
                    length="2 cm"
                x=unit_registry.Quantity(length)
                if x:
                    x=x.to("centimeter")
                length=x.magnitude
                break
            except Exception as e:
                print(e)
        while True:
            try:
                turns=Control(func=FormBuilderMkText,ptext=f"{Fore.light_green}Precision {ctx.prec}{Fore.light_yellow} number of turns? ",helpText="turns of wire",data="integer")
                if turns is None:
                    return
                elif turns in ['d',]:
                    turns=1
                LTop=decc(0.394)*decc(radius**2)*decc(turns**2)
                LBottom=(decc(9)*radius)+decc(length*10)
                L=LTop/LBottom
                print(pint.Quantity(L,'microhenry'))
                different_turns=Control(func=FormBuilderMkText,ptext=f"{Fore.light_green}Precision {ctx.prec}{Fore.light_yellow} use a different number of turns?",helpText="yes or no",data="boolean")
                if different_turns is None:
                    return
                elif different_turns in ['d',True]:
                    continue
                break
            except Exception as e:
                print(e)

        
        return pint.Quantity(L,'microhenry')

def circumference_diameter():
    with localcontext() as ctx:
        ctx.prec=int(db.detectGetOrSet("lsbld ROUNDTO default",4,setValue=False,literal=True))
        radius=0
        while True:
            try:
                diameter=Control(func=FormBuilderMkText,ptext=f"{Fore.light_green}Precision {ctx.prec}{Fore.light_yellow} diameter unit[4 cm]? ",helpText="diamater with unit",data="string")
                if diameter is None:
                    return
                elif diameter in ['d',]:
                    diameter="4 cm"
                x=unit_registry.Quantity(diameter)
                radius=pint.Quantity(decc(x.magnitude/2),x.units)
                break
            except Exception as e:
                print(e)
        if isinstance(radius,pint.registry.Quantity):
            result=decc(2*math.pi)*decc(radius.magnitude)

            return pint.Quantity(result,radius.units)
        else:
            return

def circumference_radius():
    with localcontext() as ctx:
        ctx.prec=int(db.detectGetOrSet("lsbld ROUNDTO default",4,setValue=False,literal=True))
        radius=0
        while True:
            try:
                diameter=Control(func=FormBuilderMkText,ptext=f"{Fore.light_green}Precision {ctx.prec}{Fore.light_yellow} radius unit[2 cm]? ",helpText="radius with unit",data="string")
                if diameter is None:
                    return
                elif diameter in ['d',]:
                    diameter="2 cm"
                x=unit_registry.Quantity(diameter)
                radius=pint.Quantity(decc(x.magnitude),x.units)
                break
            except Exception as e:
                print(e)
        if isinstance(radius,pint.registry.Quantity):
            result=decc(2*math.pi)*decc(radius.magnitude)

            return pint.Quantity(result,radius.units)
        else:
            return

def area_of_circle_radius():
    with localcontext() as ctx:
        ctx.prec=int(db.detectGetOrSet("lsbld ROUNDTO default",4,setValue=False,literal=True))
        '''
    A = πr²
        '''
        radius=0
        while True:
            try:
                diameter=Control(func=FormBuilderMkText,ptext=f"{Fore.light_green}Precision {ctx.prec}{Fore.light_yellow} radius unit[2 cm]? ",helpText="radius with unit",data="string")
                if diameter is None:
                    return
                elif diameter in ['d',]:
                    diameter="2 cm"
                x=unit_registry.Quantity(diameter)
                radius=pint.Quantity(decc(x.magnitude),x.units)
                break
            except Exception as e:
                print(e)
        if isinstance(radius,pint.registry.Quantity):
            result=decc(math.pi)*decc(radius.magnitude**2)

            return pint.Quantity(result,radius.units)
        else:
            return

def lc_frequency():
    with localcontext() as ctx:
        ctx.prec=int(db.detectGetOrSet("lsbld ROUNDTO default",4,setValue=False,literal=True))
        inductance=None
        capacitance=None
        while True:
            try:
                inductance=Control(func=FormBuilderMkText,ptext=f"{Fore.light_green}Precision {ctx.prec}{Fore.light_yellow} inductance(356 microhenry): ",helpText="coil inductance",data="string")
                if inductance is None:
                    return
                elif inductance in ['d',]:
                    inductance="356 microhenry"
                x=unit_registry.Quantity(inductance)
                if x:
                    x=x.to("henry")
                inductance=decc(x.magnitude,cf=20)
                break
            except Exception as e:
                print(e)
        while True:
            try:
                capacitance=Control(func=FormBuilderMkText,ptext=f"{Fore.light_green}Precision {ctx.prec}{Fore.light_yellow} capacitance[365 picofarads]? ",helpText="capacitance in farads",data="string")
                if capacitance is None:
                    return
                elif capacitance in ['d',]:
                    capacitance="365 picofarads"
                x=unit_registry.Quantity(capacitance)
                if x:
                    x=x.to("farads")
                farads=decc(x.magnitude,cf=20)
                break
            except Exception as e:
                print(e)
        frequency=1/(decc(2*math.pi)*decc(math.sqrt(farads*inductance),cf=20))
        return unit_registry.Quantity(frequency,"hertz")

def area_of_circle_diameter():
    with localcontext() as ctx:
        ctx.prec=int(db.detectGetOrSet("lsbld ROUNDTO default",4,setValue=False,literal=True))
        '''
    A = πr²
        '''
        radius=0
        while True:
            try:
                diameter=Control(func=FormBuilderMkText,ptext=f"{Fore.light_green}Precision {ctx.prec}{Fore.light_yellow} diameter unit[4 cm]? ",helpText="diamater value with unit",data="string")
                if diameter is None:
                    return
                elif diameter in ['d',]:
                    diameter="4 cm"
                x=unit_registry.Quantity(diameter)
                radius=pint.Quantity(decc(x.magnitude/2),x.units)
                break
            except Exception as e:
                print(e)
        if isinstance(radius,pint.registry.Quantity):
            result=decc(math.pi)*decc(radius.magnitude**2)

            return pint.Quantity(result,radius.units)
        else:
            return


def area_triangle():
    with localcontext() as ctx:
        ctx.prec=int(db.detectGetOrSet("lsbld ROUNDTO default",4,setValue=False,literal=True))
        height=None
        base=None
        '''
        A=hbb/2
        '''
        while True:
            try:
                base=Control(func=FormBuilderMkText,ptext="base",helpText="base width",data="string")
                if base is None:
                    return
                elif base in ['d',]:
                    base=unit_registry.Quantity('1')
                else:
                    base=unit_registry.Quantity(base)
                break
            except Exception as e:
                print(e)
                try:
                    base=Control(func=FormBuilderMkText,ptext="base no units",helpText="base width,do not include units",data="dec.dec")
                    if base is None:
                        return
                    elif base in ['d',]:
                        base=decc(1)
                    break
                except Exception as e:
                    continue

        while True:
            try:
                height=Control(func=FormBuilderMkText,ptext="height",helpText="height width",data="string")
                if height is None:
                    return
                elif height in ['d',]:
                    height=unit_registry.Quantity('1')
                else:
                    height=unit_registry.Quantity(height)
                break
            except Exception as e:
                print(e)
                try:
                    height=Control(func=FormBuilderMkText,ptext="height no units",helpText="height width, do not include units",data="dec.dec")
                    if height is None:
                        return
                    elif height in ['d',]:
                        height=decc(1)
                    break
                except Exception as e:
                    continue
        print(type(height),height,type(base))
        if isinstance(height,decimal.Decimal) and isinstance(base,decimal.Decimal):
            return decc((height*base)/decc(2))
        elif isinstance(height,pint.Quantity) and isinstance(base,pint.Quantity):
            return ((height.to(base)*base)/2)
        elif isinstance(height,pint.Quantity) and isinstance(base,decimal.Decimal):
            return ((height*unit_registry.Quantity(base,height.units))/2)
        elif isinstance(height,decimal.Decimal) and isinstance(base,pint.Quantity):
            return ((unit_registry.Quantity(height,base.units)*base)/2)

class Taxable:
    def general_taxable(self):
        taxables=[
"Alcoholic beverages",
"Books and publications",
"Cameras and film",
"Carbonated and effervescent water",
"Carbonated soft drinks and mixes",
"Clothing",
"Cosmetics",
"Dietary supplements",
"Drug sundries, toys, hardware, and household goods",
"Fixtures and equipment used in an activity requiring the holding of a seller’s permit, if sold at retail",
"Food sold for consumption on your premises (see Food service operations)",
"Hot prepared food products (see Hot prepared food products)",
"Ice",
"Kombucha tea (if alcohol content is 0.5 percent or greater by volume)",
"Medicated gum (for example, Nicorette and Aspergum)",
"Newspapers and periodicals",
"Nursery stock",
"Over-the-counter medicines (such as aspirin, cough syrup, cough drops, and throat lozenges)",
"Pet food and supplies",
"Soaps or detergents",
"Sporting goods",
"Tobacco products",
        ]
        nontaxables=[
"Baby formulas (such as Isomil)",
"Cooking wine",
"Energy bars (such as PowerBars)",
"""Food products—This includes baby food, artificial sweeteners, candy, gum, ice cream, ice cream novelties,
popsicles, fruit and vegetable juices, olives, onions, and maraschino cherries. Food products also include
beverages and cocktail mixes that are neither alcoholic nor carbonated. The exemption applies whether sold in
liquid or frozen form.""",
"Granola bars",
"Kombucha tea (if less than 0.5 percent alcohol by volume and naturally effervescent)",
"Sparkling cider",
"Noncarbonated sports drinks (including Gatorade, Powerade, and All Sport)",
"Pedialyte",
"Telephone cards (see Prepaid telephone debit cards and prepaid wireless cards)",
"Water—Bottled noncarbonated, non-effervescent drinking water",
        ]

        taxables_2=[
"Alcoholic beverages",
'''Carbonated beverages, including semi-frozen beverages
containing carbonation, such as slushies (see Carbonated fruit
juices)''',
"Coloring extracts",
"Dietary supplements",
"Ice",
"Over-the-counter medicines",
"Tobacco products",
"non-human food",
"Kombucha tea (if >= 0.5% alcohol by volume and/or is not naturally effervescent)",
        ]
        for i in taxables_2:
            if i not in taxables:
                taxables.append(i)

        ttl=[]
        for i in taxables:
            ttl.append(i)
        for i in nontaxables:
            ttl.append(i)
        htext=[]
        cta=len(ttl)
        ttl=sorted(ttl,key=str)
        for num,i in enumerate(ttl):
            htext.append(std_colorize(i,num,cta))
        htext='\n'.join(htext)
        while True:
            print(htext)
            select=Control(func=FormBuilderMkText,ptext="Please select all indexes that apply to item?",helpText=htext,data="list")
            if select is None:
                return
            for i in select:
                try:
                    index=int(i)
                    if ttl[index] in taxables:
                        return True
                except Exception as e:
                    print(e)
            return False
    def kombucha(self):
        '''determine if kombucha is taxable'''
        fd={
            'Exceeds 0.5% ABV':{
            'default':False,
            'type':'boolean',
            },
            'Is it Naturally Effervescent?':{
            'default':False,
            'type':'boolean',
            },

        }
        data=FormBuilder(data=fd)
        if data is None:
            return
        else:
            if data['Exceeds 0.5% ABV']:
                return True

            if not data['Is it Naturally Effervescent?']:
                return True

            return False
        
#tax rate tools go here
def AddNewTaxRate(excludes=['txrt_id','DTOE']):
    with localcontext() as ctx:
        ctx.prec=int(db.detectGetOrSet("lsbld ROUNDTO default",4,setValue=False,literal=True))
        with Session(ENGINE) as session:
            '''AddNewTaxRate() -> None

            add a new taxrate to db.'''
            tr=TaxRate()
            session.add(tr)
            session.commit()
            session.refresh(tr)
            fields={i.name:{
            'default':getattr(tr,i.name),
            'type':str(i.type).lower()} for i in tr.__table__.columns if i.name not in excludes
            }

            fd=FormBuilder(data=fields,passThruText=f"Precision {ctx.prec}")
            if fd is None:
                session.delete(tr)
                return
            for k in fd:
                setattr(tr,k,fd[k])

        
            session.add(tr)
            session.commit()
            session.refresh(tr)
        print(tr)
        return tr.TaxRate

def GetTaxRate(excludes=['txrt_id','DTOE']):
    with localcontext() as ctx:
        ctx.prec=int(db.detectGetOrSet("lsbld ROUNDTO default",4,setValue=False,literal=True))
        with Session(ENGINE) as session:
            '''GetTaxRate() -> TaxRate:Decimal

            search for and return a Decimal/decc
            taxrate for use by prompt.
            '''
            tr=TaxRate()
            fields={i.name:{
            'default':getattr(tr,i.name),
            'type':str(i.type).lower()} for i in tr.__table__.columns if i.name not in excludes
            }

            fd=FormBuilder(data=fields,passThruText=f"Precision {ctx.prec} ; GetTaxRate Search -> ")
            if fd is None:
                return
            for k in fd:
                setattr(tr,k,fd[k])
            #and_
            filte=[]
            for k in fd:
                if fd[k] is not None:
                    if isinstance(fd[k],str):
                        filte.append(getattr(TaxRate,k).icontains(fd[k]))
                    else:
                        filte.append(getattr(tr,k)==fd[k])
        
            results=session.query(TaxRate).filter(and_(*filte)).all()
            ct=len(results)
            htext=[]
            for num,i in enumerate(results):
                m=std_colorize(i,num,ct)
                print(m)
                htext.append(m)
            htext='\n'.join(htext)
            if ct < 1:
                print(f"{Fore.light_red}There is nothing to work on in TaxRates that match your criteria.{Style.reset}")
                return
            while True:
                select=Control(func=FormBuilderMkText,ptext="Which index to return for tax rate[NAN=0.0000]?",helpText=htext,data="integer")
                print(select)
                if select is None:
                    return
                elif isinstance(select,str) and select.upper() in ['NAN',]:
                    return 0
                elif select in ['d',]:
                    return results[0].TaxRate
                else:
                    if index_inList(select,results):
                        return results[select].TaxRate
                    else:
                        continue

def price_by_tax(total=False):
    with localcontext() as ctx:
        ctx.prec=int(db.detectGetOrSet("lsbld ROUNDTO default",4,setValue=False,literal=True))
        fields={
        'price':{
            'default':0,
            'type':'dec.dec'
            },
        'rate':{
            'default':GetTaxRate(),
            'type':'dec.dec'
            }
        }
        fd=FormBuilder(data=fields,passThruText=f"Precision {ctx.prec} ; Tax on Price ->")
        if fd is None:
            return
        else:
            price=fd['price']
            rate=fd['rate']
            if price is None:
                price=0
            if fd['rate'] is None:
                rate=0
            if total == False:
                return decc(price,cf=4)*decc(rate,cf=4)
            else:
                return (decc(price,cf=4)*decc(rate,cf=4))+decc(price,cf=4)

def price_plus_crv_by_tax(total=False):
    with localcontext() as ctx:
        ctx.prec=int(db.detectGetOrSet("lsbld ROUNDTO default",4,setValue=False,literal=True))
        fields={
        'price':{
            'default':0,
            'type':'dec.dec'
            },
        'crv_total_for_pkg':{
            'default':0,
            'type':'dec.dec',
        },
        'rate':{
            'default':GetTaxRate(),
            'type':'dec.dec'
            }
        }
        fd=FormBuilder(data=fields,passThruText=f"Precision {ctx.prec};Tax on (Price+CRV)")
        if fd is None:
            return
        else:
            price=fd['price']
            rate=fd['rate']
            crv=fd['crv_total_for_pkg']
            if price is None:
                price=0
            if crv is None:
                crv=0
            if fd['rate'] is None:
                rate=0
            if total == False:
                return (decc(price,cf=4)+decc(crv,cf=4))*decc(rate,cf=4)
            else:
                return (price+crv)+((decc(price,cf=4)+decc(crv,cf=4))*decc(rate,cf=4))

def DeleteTaxRate(excludes=['txrt_id','DTOE']):
    with Session(ENGINE) as session:
        '''DeleteTaxRate() -> None

        search for and delete selected
        taxrate.
        '''
        '''AddNewTaxRate() -> None

        add a new taxrate to db.'''
        tr=TaxRate()
        fields={i.name:{
        'default':getattr(tr,i.name),
        'type':str(i.type).lower()} for i in tr.__table__.columns if i.name not in excludes
        }
        fd=FormBuilder(data=fields)
        if fd is None:
            return
        for k in fd:
            setattr(tr,k,fd[k])
        #and_
        filte=[]
        for k in fd:
            if fd[k] is not None:
                if isinstance(fd[k],str):
                    filte.append(getattr(TaxRate,k).icontains(fd[k]))
                else:
                    filte.append(getattr(tr,k)==fd[k])
        session.commit()
    
        results=session.query(TaxRate).filter(and_(*filte)).all()
        ct=len(results)
        htext=[]
        for num,i in enumerate(results):
            m=std_colorize(i,num,ct)
            print(m)
            htext.append(m)
        htext='\n'.join(htext)
        if ct < 1:
            print(f"{Fore.light_red}There is nothing to work on in TaxRates that match your criteria.{Style.reset}")
            return
        while True:
            select=Control(func=FormBuilderMkText,ptext="Which index to delete?",helpText=htext,data="integer")
            print(select)
            if select is None:
                print(f"{Fore.light_yellow}Nothing was deleted!{Style.reset}")
                return
            elif isinstance(select,str) and select.upper() in ['NAN',]:
                print(f"{Fore.light_yellow}Nothing was deleted!{Style.reset}")
                return 0
            elif select in ['d',]:
                print(f"{Fore.light_yellow}Nothing was deleted!{Style.reset}")
                return
            else:
                if index_inList(select,results):
                    session.delete(results[select])
                    session.commit()
                    return
                else:
                    continue

def EditTaxRate(excludes=['txrt_id','DTOE']):
    '''DeleteTaxRate() -> None

    search for and delete selected
    taxrate.
    '''
    tr=TaxRate()
    fields={i.name:{
    'default':getattr(tr,i.name),
    'type':str(i.type).lower()} for i in tr.__table__.columns if i.name not in excludes
    }
    fd=FormBuilder(data=fields)
    if fd is None:
        return
    for k in fd:
        setattr(tr,k,fd[k])
    #and_
    filte=[]
    for k in fd:
        if fd[k] is not None:
            if isinstance(fd[k],str):
                filte.append(getattr(TaxRate,k).icontains(fd[k]))
            else:
                filte.append(getattr(tr,k)==fd[k])
    with Session(ENGINE) as session:
        results=session.query(TaxRate).filter(and_(*filte)).all()
        ct=len(results)
        htext=[]
        for num,i in enumerate(results):
            m=std_colorize(i,num,ct)
            print(m)
            htext.append(m)
        htext='\n'.join(htext)
        if ct < 1:
            print(f"{Fore.light_red}There is nothing to work on in TaxRates that match your criteria.{Style.reset}")
            return
        while True:
            select=Control(func=FormBuilderMkText,ptext="Which index to edit?",helpText=htext,data="integer")
            print(select)
            if select is None:
                print(f"{Fore.light_yellow}Nothing was deleted!{Style.reset}")
                return
            elif isinstance(select,str) and select.upper() in ['NAN',]:
                print(f"{Fore.light_yellow}Nothing was deleted!{Style.reset}")
                return 0
            elif select in ['d',]:
                print(f"{Fore.light_yellow}Nothing was deleted!{Style.reset}")
                return
            else:
                if index_inList(select,results):
                    fields={i.name:{
                    'default':getattr(results[select],i.name),
                    'type':str(i.type).lower()} for i in results[select].__table__.columns if i.name not in excludes
                    }
                    fd=FormBuilder(data=fields)
                    for k in fd:
                        setattr(results[select],k,fd[k])
                    session.commit()
                    session.refresh(results[select])
                    print(results[select])
                    return
                else:
                    continue

def heronsFormula():
    with localcontext() as ctx:
        ctx.prec=int(db.detectGetOrSet("lsbld ROUNDTO default",4,setValue=False,literal=True))
        '''
        Calculate the semi-perimeter (s): Add the lengths of the three sides and divide by 2.
        s = (a + b + c) / 2
        '''
        fields={
            'side 1':{
            'default':1,
            'type':'dec.dec'
            },
            'side 2':{
            'default':1,
            'type':'dec.dec'
            },
            'side 3':{
            'default':1,
            'type':'dec.dec'
            },
        }
        fd=FormBuilder(data=fields,passThruText=f"Precision {ctx.prec}")
        if fd is None:
            return

        s=(fd['side 1']+fd['side 2']+fd['side 3'])/2
        '''Apply Heron's formula: Substitute the semi-perimeter (s) and the side lengths (a, b, and c) into the formula:
        Area = √(s(s-a)(s-b)(s-c))'''
        Area=math.sqrt(s*(s-fd['side 1'])*(s-fd['side 2'])*(s-fd['side 3']))
        return Area

def volumeCylinderRadius():
    with localcontext() as ctx:
        ctx.prec=int(db.detectGetOrSet("lsbld ROUNDTO default",4,setValue=False,literal=True))
        '''
        Volume of a cylinder: Used for cylindrical storage bins, silos, or tanks.(V=pi r^{2}h)
        '''
        fields={
            'height':{
            'default':1,
            'type':'dec.dec'
            },
            'radius':{
            'default':1,
            'type':'dec.dec'
            },
        }
        fd=FormBuilder(data=fields,passThruText=f"Precision {ctx.prec}")
        if fd is None:
            return

        volume=Decimal(math.pi)*(fd['radius']**2)*fd['height']
        return volume

def volumeCylinderDiameter():
    with localcontext() as ctx:
        ctx.prec=int(db.detectGetOrSet("lsbld ROUNDTO default",4,setValue=False,literal=True))
        '''
        Volume of a cylinder: Used for cylindrical storage bins, silos, or tanks.(V=pi r^{2}h)
        '''
        fields={
            'height':{
            'default':1,
            'type':'dec.dec'
            },
            'diameter':{
            'default':1,
            'type':'dec.dec'
            },
        }
        fd=FormBuilder(data=fields,passThruText=f"Precision {ctx.prec}")
        if fd is None:
            return

        volume=Decimal(math.pi)*((fd['diameter']/2)**2)*fd['height']
        return volume

def volumeConeRadius():
    with localcontext() as ctx:
        ctx.prec=int(db.detectGetOrSet("lsbld ROUNDTO default",4,setValue=False,literal=True))
        '''
        Volume of a cylinder: Used for cylindrical storage bins, silos, or tanks.(V=pi r^{2}h)
        '''
        fields={
            'height':{
            'default':1,
            'type':'dec.dec'
            },
            'radius':{
            'default':1,
            'type':'dec.dec'
            },
        }
        fd=FormBuilder(data=fields,passThruText=f"Precision {ctx.prec}")
        if fd is None:
            return

        volume=Decimal(1/3)*(Decimal(math.pi)*(fd['radius']**2)*fd['height'])
        return volume

def volumeConeDiameter():
    with localcontext() as ctx:
        ctx.prec=int(db.detectGetOrSet("lsbld ROUNDTO default",4,setValue=False,literal=True))
        '''
        Volume of a cylinder: Used for cylindrical storage bins, silos, or tanks.(V=pi r^{2}h)
        '''
        fields={
            'height':{
            'default':1,
            'type':'dec.dec'
            },
            'diameter':{
            'default':1,
            'type':'dec.dec'
            },
        }
        fd=FormBuilder(data=fields,passThruText=f"Precision {ctx.prec}")
        if fd is None:
            return

        volume=Decimal(1/3)*(Decimal(math.pi)*((fd['diameter']/2)**2)*fd['height'])
        return volume

def volumeHemisphereRadius():
    with localcontext() as ctx:
        ctx.prec=int(db.detectGetOrSet("lsbld ROUNDTO default",4,setValue=False,literal=True))
        '''
        Volume of a hemisphere = (2/3) x 3.14 x r3
        '''
        fields={
            'radius':{
            'default':1,
            'type':'dec.dec'
            },
        }
        fd=FormBuilder(data=fields,passThruText=f"Precision {ctx.prec}")
        if fd is None:
            return

        volume=Decimal(2/3)*Decimal(math.pi)*(fd['radius']**3)
        return volume

def volumeHemisphereDiameter():
    with localcontext() as ctx:
        ctx.prec=int(db.detectGetOrSet("lsbld ROUNDTO default",4,setValue=False,literal=True))
        '''
        Volume of a hemisphere = (2/3) x 3.14 x r3
        '''
        fields={
            'diameter':{
            'default':1,
            'type':'dec.dec'
            },
        }
        fd=FormBuilder(data=fields,passThruText=f"Precision {ctx.prec}")
        if fd is None:
            return

        volume=Decimal(2/3)*Decimal(math.pi)*((fd['diameter']/2)**3)
        return volume

def areaCircleDiameter():
    with localcontext() as ctx:
        ctx.prec=int(db.detectGetOrSet("lsbld ROUNDTO default",4,setValue=False,literal=True))
        '''
        Volume of a hemisphere = (2/3) x 3.14 x r3
        '''
        fields={
            'diameter':{
            'default':1,
            'type':'dec.dec'
            },
        }
        fd=FormBuilder(data=fields,passThruText=f"Precision {ctx.prec}")
        if fd is None:
            return

        volume=Decimal(math.pi)*((fd['diameter']/2)**2)
        return volume


def areaCircleRadius():
    with localcontext() as ctx:
        ctx.prec=int(db.detectGetOrSet("lsbld ROUNDTO default",4,setValue=False,literal=True))
        '''
        Volume of a hemisphere = (2/3) x 3.14 x r3
        '''
        fields={
            'radius':{
            'default':1,
            'type':'dec.dec'
            },
        }
        fd=FormBuilder(data=fields,passThruText=f"Precision {ctx.prec}")
        if fd is None:
            return

        volume=Decimal(math.pi)*((fd['radius'])**2)
        return volume

###newest
def circumferenceCircleRadiu():
    #get the circumference of a circle using radius
    with localcontext() as ctx:
        ctx.prec=int(db.detectGetOrSet("lsbld ROUNDTO default",4,setValue=False,literal=True))
        '''
        2πr
        '''
        fields={
            'radius':{
            'default':1,
            'type':'dec.dec'
            },
        }
        fd=FormBuilder(data=fields,passThruText=f"Precision {ctx.prec}")
        if fd is None:
            return

        circumference=2*Deimal(math.pi)*fd['radius']
        return circumference

def circumferenceCircleDiameter():
    #get the circumference of a circle using diameter
    with localcontext() as ctx:
        ctx.prec=int(db.detectGetOrSet("lsbld ROUNDTO default",4,setValue=False,literal=True))
        '''
        2π(d/2)
        '''
        fields={
            'diameter':{
            'default':1,
            'type':'dec.dec'
            },
        }
        fd=FormBuilder(data=fields,passThruText=f"Precision {ctx.prec}")
        if fd is None:
            return

        circumference=2*Deimal(math.pi)*Decimal(fd['diameter']/2)
        return circumference

def sudokuCandidates():
    #get the circumference of a circle using diameter
    with localcontext() as ctx:
        ctx.prec=int(db.detectGetOrSet("lsbld ROUNDTO default",4,setValue=False,literal=True))
        '''
        2π(d/2)
        '''
        gameSymbols=Control(func=FormBuilderMkText,ptext="Game symbols [123456789]",helpText="123456789",data="string")
        if gameSymbols in ['NaN',None,]:
            return
        elif gameSymbols in ['d',]:
            gameSymbols='123456789'

        fields={
            'Symbols for Row':{
            'default':'',
            'type':'string'
            },
            'Symbols for Column':{
            'default':'',
            'type':'string'
            },
            'Symbols for Cell':{
            'default':'',
            'type':'string'
            },
            'Symbols for Right-Diagnal':{
            'default':'',
            'type':'string'
            },
            'Symbols for Left-Diagnal':{
            'default':'',
            'type':'string'
            },
        }
        loop=True
        while loop:
            fd=FormBuilder(data=fields,passThruText=f"Sudoku Candidates? ")
            if fd is None:
                return
            
            sString=[]
            for i in fd:
                if isinstance(fd[i],str):
                    sString.append(fd[i])
            sString=' '.join(sString)
            cd=[]
            for i in gameSymbols:
                if i not in sString:
                    cd.append(i)
            print(cd)
            loop=Control(func=FormBuilderMkText,ptext="Again?",helpText="yes or no/boolean",data="boolean")
            if loop in ['NaN',None]:
                return
            elif loop in ['d',True]:
                loop=True
            else:
                return cd
'''
Ellipse: area=πab
, where 2a
 and 2b
 are the lengths of the axes of the ellipse.

Sphere: vol=4πr3/3
, surface area=4πr2
.

Cylinder: vol=πr2h
, lateral area=2πrh
, total surface area=2πrh+2πr2
.


Cone: vol=πr2h/3
, lateral area=πrr2+h2−−−−−−√
, total surface area=πrr2+h2−−−−−−√+πr2
'''

class candidates:
    def __new__(self,test=False):
        n=None
        symbols=[i for i in '123456789']
        none_symbol='0'

        if test:
            pzl={
            'l1':[1,n,9,n,n,3,7,n,8],
            'l2':[n,n,4,n,n,n,3,n,2],
            'l3':[3,n,5,n,6,8,1,9,4],
            'l4':[6,n,7,8,1,n,n,n,n],
            'l5':[9,3,1,n,n,n,5,8,n],
            'l6':[n,n,2,3,n,n,6,n,n],
            'l7':[n,n,8,n,n,5,n,3,n],
            'l8':[4,n,3,n,8,6,n,1,n],
            'l9':[n,9,6,n,n,n,n,n,7],
            }


        def mkpuzl():
            while True:
                done={}
                htext=[]
                symbols='123456789'
                ct=len(symbols)
                for num,i in enumerate(symbols):
                    htext.append(std_colorize(i,num,ct))
                    done[f'l{num+1}']={
                        'default':[],
                        'type':'list'
                    }
                finished=FormBuilder(data=done,passThruText=f"enter chars. of {symbols}, use 0 to represent an unfilled cell: Must be 9-Long")
                if finished is None:
                    return None
                else:
                    for i in finished:
                        if len(finished[i]) != 9:
                            continue
                        for num,ii in enumerate(finished[i]):
                            if ii == '0':
                                finished[i][num]=n
                    return finished


                #select a list of 9 symbols for ln#
                #symbol is 0, then symbol is None
                #append list to final list
                #for 9lines of 9elements per 1 line as a dict of 9 keys with 9 lists that are 9 elements long
        if not test:
            pzl=mkpuzl()

        while True:
            #print(pzl)
            if pzl is None:
                return
            mapped={
                'block1=':{
                    'rows':[0,1,2],
                    'columns':[0,1,2]
                },
                'block2':{
                    'rows':[0,1,2],
                    'columns':[3,4,5]
                },
                'block3':{
                    'rows':[0,1,2],
                    'columns':[4,5,6]
                },
                'block4':{
                    'rows':[3,4,5],
                    'columns':[0,1,2]
                },
                'block5':{
                    'rows':[3,4,5],
                    'columns':[3,4,5]
                },
                'block6':{
                    'rows':[3,4,5],
                    'columns':[6,7,8]
                },
                'block7':{
                    'rows':[6,7,8],
                    'columns':[0,1,2]
                },
                'block8':{
                    'rows':[6,7,8],
                    'columns':[3,4,5]
                },
                'block9':{
                    'rows':[6,7,8],
                    'columns':[6,7,8]
                },
            }

            def rx2idx(line,column,x_limit=9,y_limit=9):
                return ((x_limit*line)-(y_limit-column))

            def desired(block_x=[1,4],block_y=[1,4],num=''): 
                iblock_x=block_x
                iblock_x[-1]+=1

                iblock_y=block_y
                iblock_y[-1]+=1
                for i in range(*iblock_x):
                    for x in range(*iblock_y):
                        #print(f'block{num}',rx2idx(i,x))
                        yield rx2idx(i,x)
                        
            rgrid=[
            [[1,3],[1,3]],[[1,3],[4,6]],[[1,3],[7,9]],
            [[4,6],[1,3]],[[4,6],[4,6]],[[4,6],[7,9]],
            [[7,9],[1,3]],[[7,9],[4,6]],[[7,9],[7,9]],
            ]
            grid={}
            for num,y in enumerate(rgrid):
                grid[f'block{num+1}']=[i for i in desired(y[0],y[1],num+1)]

            #grid=mkgrid()
            def characters_row(row):
                tmp=''
                for i in row:
                    if i!=None:
                        tmp+=str(i)
                return tmp


            def characters_column(rows,column):
                tmp=''
                x=[]
                for r in rows:
                    c=rows[r][column]
                    if c is not None:
                        if not isinstance(c,list):
                            tmp+=str(c)
                return tmp

            def characters_block(pzl,mapped,ttl):
                tmp=''
                zz=[]
                for i in pzl:
                    zz.extend(pzl[i])
                ttl+=1
                #print(ttl,'ttl')
                for i in grid:
                    if ttl in grid[i]:
                        for x in grid[i]:
                            #print(x-1)
                            if zz[x-1] is not None:
                                tmp+=str(zz[x-1])
                            
                #back to the drawng board
                return tmp

            def display_candidates(pzl):
                ttl=0
                newStart=None
                while True:
                    ttl=0
                    for numRow in enumerate(pzl):
                        for COL in range(len(pzl[numRow[-1]])):
                            if ttl > 81:
                                ttl=0
                            filled=''
                            tmp=[]
                            ROW=[i for i in reversed(numRow)]
                            consumed=f"{characters_row(pzl[ROW[0]])}{characters_column(pzl,COL)}{characters_block(pzl,mapped,ttl)}"
                            tmpl=[]
                            for x in stre(consumed)/1:
                                if x not in tmpl:
                                    tmpl.append(x)
                            tmpl=sorted(tmpl)
                            fmsg=f'''Percent(({ttl}/80)*100)->{(ttl/80)*100:.2f} RowCol({Fore.orange_red_1}R={ROW[-1]},{Fore.light_steel_blue}C={COL})
    {Fore.light_green}Reduced("{consumed}")->"{''.join(tmpl)}"'''
                            symbol_string=f"""{fmsg}{Fore.light_yellow}
    NoneSymbol({none_symbol}){Fore.light_steel_blue}
    SYMBOL({pzl[numRow[-1]][COL]}) 
    ROWS({ROW[-1]}): {characters_row(pzl[ROW[0]])} 
    COLUMN({COL}): {characters_column(pzl,COL)} 
    BLOCK: '{characters_block(pzl,mapped,ttl)}' """
                            for char in symbols:
                                if char not in tmpl:
                                    tmp.append(char)
                            candidates=', '.join(tmp)
                            color=''
                            color_end=''
                            if len(candidates) == 1:
                                color=f"{Fore.light_green}"
                                color_end=f"{Style.reset}"
                                if pzl[numRow[-1]][COL] != candidates and pzl[numRow[-1]][COL] is not None:
                                    filled=f"{Fore.orange_red_1}AlreadyFilled({pzl[numRow[-1]][COL]}){Style.reset}"
                                    color_end=filled+color_end
                                    candidates=''
                            elif len(candidates) <= 0:
                                color=f"{Fore.light_red}"
                                if pzl[numRow[-1]][COL] is not None:
                                    filled=f"{Fore.orange_red_1}AlreadyFilled({pzl[numRow[-1]][COL]}){Style.reset}"
                                    color_end=filled+color_end
                                else:
                                    color_end=f"{filled} No candidates were found!{Style.reset}"
                            elif len(candidates) >= 1:
                                color=f"{Fore.light_cyan}"
                                color_end=f"{Style.reset}"
                                if pzl[numRow[-1]][COL] != candidates and pzl[numRow[-1]][COL] is not None:
                                    filled=f"{Fore.orange_red_1}AlreadyFilled({pzl[numRow[-1]][COL]}){Style.reset}"
                                    color_end=filled+color_end
                                    candidates=''
                            ttl+=1
                            if newStart is not None:
                                if ttl < newStart:
                                    continue
                                else:
                                    newStart=None
                            print(symbol_string)
                            print(f"{color}CANDIDATES: {color_end}",candidates)
                            
                            page=Control(func=lambda text,data:FormBuilderMkText(text,data,passThru=['goto',],PassThru=True),ptext="Next?",helpText="yes or no,",data="boolean")
                            if page in [None,'NaN']:
                                return
                            elif page in ['d',]:
                                pass
                            elif page in ['goto']:
                                breakMe=False
                                while True:
                                    stopAt=Control(func=FormBuilderMkText,ptext="Goto where?",helpText="0-81",data="integer")
                                    if stopAt in ['NaN',None]:
                                        return
                                    elif stopAt in [i for i in range(0,82)]:
                                        newStart=stopAt
                                        breakMe=True
                                        break
                                    else:
                                        print("between 0 and 81")
                                        continue
                                if breakMe:
                                    break

                            

                print('ROW and COL/COLUM are 0/zero-indexed!')
            display_candidates(pzl)
            control=Control(func=FormBuilderMkText,ptext="new data/nd,re-run/rr[default]",helpText='',data="string")
            if control in [None,'NaN']:
                return
            elif control in ['d','rr','re-run','re run']:
                continue
            elif control in ['new data','new-data','nd']:
                pzl=mkpuzl()
                continue
            else:
                continue


def costToRun():
    fields={
    'wattage of device plugged in, turned on/off?':{
        'default':60,
        'type':'float'
    },
    'hours of use?':{
        'default':1,
        'type':'float'
    },
    'electrical providers cost per kWh':{
        'default':0.70  ,
        'type':'float'
    },
    }

    fd=FormBuilder(data=fields)
    if fd is None:
        return
   
    cost=((fd['wattage of device plugged in, turned on/off?']/1000)*fd['electrical providers cost per kWh'])
    total_cost_to=cost*fd['hours of use?']
    return total_cost_to


def generic_service_or_item():
    fields={
    'PerBaseUnit':{
        'default':'squirt',
        'type':'string',
        },
    'PerBaseUnit_is_EquivalentTo[Conversion]':{
        'default':'1 squirt == 2 grams',
        'type':'string',
        },
    'PricePer_1_EquivalentTo[Conversion]':{
        'default':0,
        'type':'float',
        },
    'Name or Description':{
        'default':'dawn power wash',
        'type':'string'
        },
    'Cost/Price/Expense Taxed @ %':{
        'default':'Item was purchased for 3.99 Taxed @ 6.3% (PRICE+(PRICE+TAX))',
        'type':'string'
        },
    'Where was the item purchased/sold[Location/Street Address, City, State ZIP]?':{
        'default':'walmart in gloucester va, 23061',
        'type':'string'
        },
    }
    fd=FormBuilder(data=fields)
    if fd is not None:
        textty=[]
        cta=len(fd)
        for num,k in enumerate(fd):
            msg=f"{k} = '{fd[k]}'"
            textty.append(strip_colors(std_colorize(msg,num,cta)))
        master=f'''
Non-Std Item/Non-Std Service
----------------------------
{' '+'\n '.join(textty)}
----------------------------
        '''
        return master

def reciept_book_entry():
    fields={
    'reciept number':{
        'default':'',
        'type':'string'
    },
    'reciept dtoe':{
        'default':datetime.now(),
        'type':'datetime'
    },
    'recieved from':{
        'default':'',
        'type':'string'
    },
    'address':{
        'default':'',
        'type':'string'
    },
    'Amount ($)':{
        'default':0,
        'type':'dec.dec',
    },
    'For':{
        'default':'',
        'type':'string'
    },
    'By':{
        'default':'',
        'type':'string'
    },
    'Amount of Account':{
        'default':0,
        'type':'dec.dec',
    },
    'Amount Paid':{
        'default':0,
        'type':'dec.dec',
    },
    'Balance Due':{
        'default':0,
        'type':'dec.dec',
    },
    'Cash':{
        'default':0,
        'type':'dec.dec',
    },
    'Check':{
        'default':0,
        'type':'dec.dec',
    },
    'Money Order':{
        'default':0,
        'type':'dec.dec',
    },
    'Line 1':{
        'default':'',
        'type':'string'
    },
    'Line 2':{
        'default':'',
        'type':'string'
    },
    'Notes':{
        'default':'',
        'type':'string'
    },
    'Filing Location Id':{
        'default':'',
        'type':'string'
    },
    }
    fd=FormBuilder(data=fields)
    if fd is not None:
        textty=[]
        cta=len(fd)
        for num,k in enumerate(fd):
            msg=f"{k} = '{fd[k]}'"
            textty.append(strip_colors(std_colorize(msg,num,cta)))
        master=f'''
Reciept {fd['reciept number']}
----------------------------
{' '+'\n '.join(textty)}
----------------------------
        '''
        return master

def nowToPercentTime(now=None):
    if not isinstance(now,datetime):
        now=datetime.now()
    today=datetime(now.year,now.month,now.day)
    diff=now-today
    a=round(diff.total_seconds()/60/60/24,6)
    a100=round(a*100,2)
    m=str(now.strftime(f'{now} | %mM/%dD/%YY @ %H(24H)/%I %p(12H):%M:%S | {a100} Percent of 24H has passed since {today} as {diff.total_seconds()} seconds passed/{(24*60*60)} total seconds in day={a}*100={a100} | Percent of Day Passed = {a100}%'))
    return m


def ndtp():
    msg=''
    while True:
        try:
            fields={
                'distance':{
                'type':'float',
                'default':25,
                },
                'speed':{
                'type':'float',
                'default':70
                },
                'total break time':{
                'type':'string',
                'default':'10 minutes'
                }
            }
            fd=FormBuilder(data=fields,passThruText=msg)
            if fd is None:
                return
            
            mph=fd['speed']
            distance=fd['distance']
            try:
                breaks=pint.Quantity(fd['total break time']).to('seconds').magnitude
            except Exception as e:
                breaks=pint.Quantity(fd['total break time']+' minutes').to('seconds').magnitude
            duration=pint.Quantity(distance/mph,'hour').to('sec').magnitude
            #12 minutes 
            buffer=timedelta(minutes=15)
            original=timedelta(seconds=duration)+timedelta(seconds=breaks)
            duration=timedelta(seconds=original.total_seconds()+buffer.total_seconds())
            now=datetime.now()
            then=now+duration
            msg=[]
            msg.append(f'Rate of Travel: {str(mph)}')
            msg.append(f'Distance To Travel: {distance}')
            msg.append(f"Now: {now}")
            msg.append(f'Non-Buffered Duration {original}')
            msg.append(f'Buffered: {duration} (+{buffer})')
            msg.append(f"Then: {then}")
            msg.append(f'Total Break Time: {timedelta(seconds=breaks)}')
            msg.append(f"From: {nowToPercentTime(now)}")
            msg.append(f"To: {nowToPercentTime(then)}")
            msg='\n\n'.join(msg)
            return msg
        except Exception as e:
            print(e)

def drug_text():
    while True:
        try:
            drug_names=[
            'thc flower',
            'thc vape',

            'thca flower',
            'thca vape',

            'caffiene',
            'caffiene+taurine',
            'caffiene+beta_alanine',

            'alcohol',
            'alcohol+thc flower',
            'alcohol+thca flower',
            
            'caffiene+thca flower+menthol',
            'caffiene+thc flower+menthol',
            ]
            extra_drugs=detectGetOrSet("extra_drugs","extra_drugs.csv",setValue=False,literal=True)
            if extra_drugs:
                extra_drugs=Path(extra_drugs)


                if extra_drugs.exists():
                    with extra_drugs.open("r") as fileio:
                        reader=csv.reader(fileio,delimiter=',')
                        for line in reader:
                            for sub in line:
                                if sub not in ['',]:
                                    drug_names.append(sub)
                                    


            htext=[]
            cta=len(drug_names)
            for num,i in enumerate(drug_names):
                htext.append(std_colorize(i,num,cta))
            htext='\n'.join(htext)
            print(htext)
            which=Control(func=FormBuilderMkText,ptext="which index?",helpText=htext,data="integer")
            if which in [None,'NaN']:
                return

            return drug_names[which]
        except Exception as e:
            print(e)
            continue

def TotalCurrencyFromMass():
    msg=''
    while True:
        try:
            fields={
                '1 Unit Mass(Grams)':{
                'type':'dec.dec',
                'default':2.50,
                },
                '1 Unit Value($)':{
                'type':'dec.dec',
                'default':0.01
                },
                'Total Unit Mass (Total Coin/Bill Mass)':{
                'type':'dec.dec',
                'default':0.0
                }
            }
            fd=FormBuilder(data=fields,passThruText=msg)
            if fd is None:
                return
            value=(decc(1/fd['1 Unit Mass(Grams)'])*decc(fd['1 Unit Value($)']))*decc(fd['Total Unit Mass (Total Coin/Bill Mass)'])
            return value
        except Exception as e:
            print(e)

def BaseCurrencyValueFromMass():
    msg=''
    while True:
        try:
            fields={
                '1 Unit Mass(Grams)':{
                'type':'dec.dec',
                'default':2.50,
                },
                '1 Unit Value($)':{
                'type':'dec.dec',
                'default':0.01
                }
            }
            fd=FormBuilder(data=fields,passThruText=msg)
            if fd is None:
                return
            value=(decc(1/fd['1 Unit Mass(Grams)'])*decc(fd['1 Unit Value($)']))
            return value
        except Exception as e:
            print(e)


def USCurrencyMassValues():
    while True:
        try:
            drug_names={
            'Mass(Grams) - 1 Dollar Coin/1.0':decc(8.1),
            'Mass(Grams) - Half Dollar/0.50':decc(11.340),
            'Mass(Grams) - Quarter/0.25':decc(5.670),
            'Mass(Grams) - Nickel/0.05':decc(5.0),
            'Mass(Grams) - Dime/0.10':decc(2.268),
            'Mass(Grams) - Penny/0.01':decc(2.5),
            'Mass(Grams) - Bill($1/$2/$5/$10/$20/$50/$100':decc(1),

            'Value for Mass(Grams) - 1 Dollar Coin/8.1 Grams':1.00,
            'Value for Mass(Grams) - Half Dollar/11.340 Grams':0.50,
            'Value for Mass(Grams) - Quarter/5.670 Grams':0.25,
            'Value for Mass(Grams) - Nickel/5 Grams':0.05,
            'Value for Mass(Grams) - Dime/2.268 Grams':0.10,
            'Value for Mass(Grams) - Penny/2.5 Grams':0.01,
            'Value for Mass(Grams) - 1$ Bill/1 Grams':1,
            'Value for Mass(Grams) - 2$ Bill/1 Grams':2,
            'Value for Mass(Grams) - 5$ Bill/1 Grams':5,
            'Value for Mass(Grams) - 10$ Bill/1 Grams':10,
            'Value for Mass(Grams) - 20$ Bill/1 Grams':20,
            'Value for Mass(Grams) - 50$ Bill/1 Grams':50,
            'Value for Mass(Grams) - 100$ Bill/1 Grams':100,
            }
            

            keys=[]
            htext=[]
            cta=len(drug_names)
            for num,i in enumerate(drug_names):
                msg=f'{i} -> {drug_names[i]}'
                htext.append(std_colorize(msg,num,cta))
                keys.append(i)
            htext='\n'.join(htext)
            print(htext)
            which=Control(func=FormBuilderMkText,ptext="which index?",helpText=htext,data="integer")
            if which in [None,'NaN']:
                return
            return drug_names[keys[which]]
            
        except Exception as e:
            print(e)
            continue


def golden_ratio():
    msg=''
    while True:
        try:
            fields={
                'measurement':{
                'type':'dec.dec',
                'default':48,
                },
            }
            fd=FormBuilder(data=fields,passThruText=msg)
            if fd is None:
                return
            side1_value=(decc(fd['measurement'])/decc(scipy.constants.golden_ratio))
            side2_value=fd['measurement']-decc(side1_value)
            which=Control(func=FormBuilderMkText,ptext=f"Which side do you wish to return [for a side of {fd['measurement']}: side1_value={side1_value},side2_value={side2_value}]?",helpText="yes/1/true=side 1,side 2 is false/no/0",data="boolean")
            if which in [None,"NaN"]:
                return
            elif which:
                return side1_value
            else:
                return side2_value
        except Exception as e:
            print(e)


def currency_conversion():
    cvt_registry=pint.UnitRegistry()
    
    definition=f'''
    USD = [currency]
    US_Dollar = nan USD
    Argentine_Peso = nan USD
    Australian_Dollar = nan USD
    Bahraini_Dinar = nan USD
    Botswana_Pula = nan USD
    Brazilian_Real = nan USD
    British_Pound = nan USD
    Bruneian_Dollar = nan USD
    Bulgarian_Lev = nan USD
    Canadian_Dollar = nan USD
    Chilean_Peso = nan USD
    Chinese_Yuan_Renminbi = nan USD
    Colombian_Peso = nan USD
    Czech_Koruna = nan USD
    Danish_Krone = nan USD
    Emirati_Dirham = nan USD
    Euro = nan USD
    Hong_Kong_Dollar = nan USD
    Hungarian_Forint = nan USD
    Icelandic_Krona = nan USD
    Indian_Rupee = nan USD
    Indonesian_Rupiah = nan USD
    Iranian_Rial = nan USD
    Israeli_Shekel = nan USD
    Japanese_Yen = nan  USD
    Kazakhstani_Tenge = nan USD
    Kuwaiti_Dinar = nan USD
    Libyan_Dinar = nan USD
    Malaysian_Ringgit = nan USD
    Mauritian_Rupee = nan USD
    Mexican_Peso =  nan USD
    Nepalese_Rupee = nan USD
    New_Zealand_Dollar = nan USD
    Norwegian_Krone = nan USD
    Omani_Rial = nan USD
    Pakistani_Rupee = nan USD
    Philippine_Peso = nan USD
    Polish_Zloty = nan USD
    Qatari_Riyal = nan USD
    Romanian_New_Leu = nan USD
    Russian_Ruble = nan USD
    Saudi_Arabian_Riyal = nan USD
    Singapore_Dollar = nan USD
    South_African_Rand = nan USD
    South_Korean_Won = nan USD
    Sri_Lankan_Rupee = nan USD
    Swedish_Krona = nan USD
    Swiss_Franc = nan USD
    Taiwan_New_Dollar = nan USD
    Thai_Baht = nan USD
    Trinidadian_Dollar = nan USD
    Turkish_Lira = nan USD
    updated_timestamp = nan USD

@context FX
    updated_timestamp = {datetime.now().timestamp()} USD
    US_Dollar = 1.00 USD
    Euro = 0.860073 USD
    British_Pound = 0.751344 USD
    Indian_Rupee = 87.844600 USD
    Australian_Dollar = 1.535853 USD
    Canadian_Dollar = 1.399527 USD
    Singapore_Dollar = 1.298947 USD
    Swiss_Franc = 0.795745 USD
    Malaysian_Ringgit = 4.223803 USD
    Japanese_Yen = 152.785472 USD
    Chinese_Yuan_Renminbi = 7.121297 USD
    Argentine_Peso = 1489.257156 USD
    Bahraini_Dinar = 0.376000 USD
    Botswana_Pula  = 14.277139 USD
    Brazilian_Real = 5.389771 USD
    Bruneian_Dollar = 1.298947 USD
    Bulgarian_Lev = 1.682157 USD
    Chilean_Peso = 941.970320 USD
    Colombian_Peso = 3863.004454 USD
    Czech_Koruna = 20.923500 USD
    Danish_Krone = 6.425020 USD
    Emirati_Dirham = 3.672500 USD
    Hong_Kong_Dollar = 7.769953 USD
    Hungarian_Forint = 335.497421 USD
    Icelandic_Krona = 123.168912 USD
    Indonesian_Rupiah = 16612.196004 USD
    Iranian_Rial = 42059.932897 USD
    Israeli_Shekel = 3.281546 USD
    Kazakhstani_Tenge = 537.743109 USD
    Kuwaiti_Dinar = 0.306634 USD
    Libyan_Dinar = 5.439986 USD
    Mauritian_Rupee = 45.517085 USD
    Mexican_Peso = 18.456530 USD
    Nepalese_Rupee = 140.617244 USD
    New_Zealand_Dollar = 1.738975 USD
    Norwegian_Krone = 10.009484 USD
    Omani_Rial = 0.384100 USD
    Pakistani_Rupee = 283.198574 USD
    Philippine_Peso  = 58.767006 USD
    Polish_Zloty = 3.649413 USD
    Qatari_Riyal = 3.640000 USD
    Romanian_New_Leu = 4.374589 USD
    Russian_Ruble = 79.626716 USD
    Saudi_Arabian_Riyal = 3.750000 USD
    South_African_Rand = 17.261565 USD
    South_Korean_Won = 1438.911643 USD
    Sri_Lankan_Rupee = 303.675738 USD
    Swedish_Krona = 9.403150 USD
    Taiwan_New_Dollar = 30.848390 USD
    Thai_Baht = 32.674978 USD
    Trinidadian_Dollar = 6.798339 USD
    Turkish_Lira = 41.965164 USD
@end'''.lower()
    defFile=db.detectGetOrSet("currency_definitions_file","currency_definitions.txt",setValue=False,literal=True)
    if defFile is None:
        return
    defFile=Path(defFile)
    with open(defFile,"w") as out:
        out.write(definition)
    cvt_registry.load_definitions(defFile)
    with cvt_registry.context("fx") as cvtr:  
        while True:  
            try:
                htext=[]
                definition=definition.split("@context FX")[-1].replace('\n@end','')
                cta=len(definition.split("\n"))
                formats='\n'.join([std_colorize(i,num,cta) for num,i in enumerate(definition.split("\n"))])
                
                formats=f'''Conversion Formats are:\n{formats}\n'''
                fields={
                'value':{
                    'default':1,
                    'type':'float',
                },
                'FromString':{
                    'default':'USD',
                    'type':'string',
                },
                'ToString':{
                    'default':'Euro',
                    'type':'string'
                },
                }
                fb=FormBuilder(data=fields,passThruText=formats)
                if fb is None:
                    return

                return_string=fb['ToString'].lower()
                value_string=f"{fb['value']} {fb['FromString']}".lower()
                resultant=cvtr.Quantity(value_string).to(return_string)

                #if it gets here return None
                return resultant
            except Exception as e:
                print(e)