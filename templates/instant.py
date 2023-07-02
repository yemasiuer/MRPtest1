#from __future__ import division
import numpy as np
from InstanceReader import InstanceReader
from Constants import Constants
import csv
import math

class TemplemeierInstanceReader( InstanceReader ):

    # Constructor
    def __init__( self, instance ):
        InstanceReader.__init__(self, instance)
        self.DTFile = None
        self.DatFile = None
        self.TMPFile = None
        self.TBOFile = None
        self.CapFile = None
        self.Filename = ""

    def ReadProductList(self):
        self.Instance.NrProduct = int( self.DatFile[0][0] )
        self.Instance.ProductName = ["" for i in range(self.Instance.NrProduct)]
        for i in range(  self.Instance.NrProduct ):
               self.Instance.ProductName[i] = self.DatFile[i +1  ][0]

        if Constants.Debug:
            print "product names %r"%self.Instance.ProductName



    #This function onpen the file generated by Templemeier
    def ReadTemplmeierFile(self, filename):
        csvfile = open(filename, 'rb')
        data_reader= csv.reader(csvfile, delimiter=" ", skipinitialspace=True)
        result = []
        for row in data_reader:
            result.append(row)
        return result
    #Create datasets from the sheets
        # Open the file to build the instance from Templeier1996

    def OpenFiles(self, instancename):
        print "open the files associated with the instance %s" % instancename

        namedtfile = list("G_041___.DT1")
        namedtfile[0] = instancename[0]
        namedtfile[2] = instancename[2]
        namedtfile[3] = instancename[3]
        namedtfile[4] = instancename[4]
        namedtfile[11] = instancename[7]
        namedtfile = "".join(namedtfile)
        self.DTFile = self.ReadTemplmeierFile( "./Instances/TempleMeierFiles/PROBA/%s"%namedtfile )

        namedatfile = list("G5______.DAT")
        namedatfile[0] = instancename[0]
        namedatfile[1] = instancename[1]
        namedatfile = "".join(namedatfile)
        self.DatFile = self.ReadTemplmeierFile( "./Instances/TempleMeierFiles/PROBA/%s"%namedatfile )


        nametmpfile = list(instancename + ".TMP")
        nametmpfile = "".join(nametmpfile)
        self.TMPFile  = self.ReadTemplmeierFile( "./Instances/TempleMeierFiles/PROBA/%s" %nametmpfile )

        nametbofile = list("K_____1_.TBO")
        nametbofile[0] = instancename[0]
        nametbofile[6] = instancename[6]
        nametbofile = "".join(nametbofile)
        self.TBOFile = self.ReadTemplmeierFile("./Instances/TempleMeierFiles/PROBA/%s" %nametbofile )

        namecapfile = list("G004_2__.CAP")
        namecapfile[0] = instancename[0]
        namecapfile[1] = instancename[1]
        namecapfile[2] = instancename[2]
        namecapfile[3] = instancename[3]
        namecapfile[5] = instancename[5]
        namecapfile = "".join(namecapfile)
        self.CapFile = self.ReadTemplmeierFile("./Instances/TempleMeierFiles/PROBA/%s" % namecapfile)


    def ReadNrResource(self):
        self.Instance.NrResource = int( self.TMPFile[1][5] )

    # Compute the requireement from the supply chain. This set of instances assume the requirement of each arc is 1.
    def CreateRequirement(self):
        self.Instance.Requirements = [[0] * self.Instance.NrProduct for _ in self.Instance.ProductSet]

        startrequirement = self.Instance.NrProduct + 1
        endrequirement = len( self.DatFile ) - 1

        for i in range(startrequirement, endrequirement):
                self.Instance.Requirements [ int( self.DatFile [i][0] ) - 1 ][ int( self.DatFile [i][1] ) - 1 ] =  float( self.DatFile [i][2] ) #in the file product are name from 1 to 10, we use 0 to 9

        if Constants.Debug:
            print "Requirement: %r" % self.Instance.Requirements


    def GetEchelonHoldingCost( self, e="n" ):
        self.Level = self.GetProductLevel()
        result = [ 0 for p in self.Instance.ProductSet ]
        if e == "l":
            for p in self.Instance.ProductSet:
                 if  self.Level[p] == 0:
                     result[p] = 10
                 if self.Level[p] == 1:
                     result[p] = 1
                 if self.Level[p] == 2:
                     result[p] = 0.1

        if e == "l2":
            for p in self.Instance.ProductSet:
                 if  self.Level[p] == 0:
                     result[p] = 2
                 if self.Level[p] == 1:
                     result[p] = 1
                 if self.Level[p] == 2:
                     result[p] = 0.5

        if e == "n":
            result = [  float( self.DatFile[i +1  ][2] ) for i in  self.Instance.ProductSet ]
        return result

    # def GenerateHoldingCostCost(self):
    #
    #     startholding = 4 +  self.Instance.NrProduct
    #
    #     self.Instance.InventoryCosts = [0.0] * self.Instance.NrProduct
    #
    #     for p in self.Instance.ProductSet:
    #         self.Instance.InventoryCosts[p] = float(self.TMPFile[startholding + p][0])



    def GetProductLevel(self):
        result = [ 0 for i in  self.Instance.ProductSet ]
        existdeeperproduct = True

        while existdeeperproduct :
            existdeeperproduct = False
            for p  in self.Instance.ProductSet:
                for q in self.Instance.ProductSet:
                    if self.Instance.Requirements[p][q] > 0 and  result[q] <= result[p]:
                        result[q] = result[p] + 1
                        existdeeperproduct = True

        return result

    def GenerateTimeHorizon(self, largetimehorizon = False):
        self.Instance.ComputeLevel()
        self.Instance.ComputeMaxLeadTime()
        self.Instance.ComputeIndices()

        self.Instance.NrTimeBucketWithoutUncertaintyBefore = self.Instance.MaxLeadTime
        self.Instance.NrTimeBucketWithoutUncertaintyAfter = 0#self.Instance.MaxLeadTime
        self.Instance.NrTimeBucket = self.Instance.NrTimeBucketWithoutUncertaintyBefore  + self.Instance.NrTimeBucketWithoutUncertaintyAfter + int(self.TMPFile[1][1])

        # Consider a time horizon of 20 days plus the total lead time
        if largetimehorizon:
            self.Instance.NrTimeBucket = self.Instance.NrTimeBucketWithoutUncertaintyBefore + self.Instance.NrTimeBucketWithoutUncertaintyAfter + 10

        self.Instance.ComputeIndices()



    def GenerateDistribution(self, forecasterror, rateknown = 90, longtimehorizon= False):

            finishproduct = self.GetfinishProduct()

            self.Instance.YearlyAverageDemand = [ int( self.DTFile[0][p] ) if p in finishproduct else 0 for p in self.Instance.ProductSet ]
            self.Instance.YearlyStandardDevDemands = [ 0 for p in self.Instance.ProductSet]

            stationarydistribution = self.IsStationnaryDistribution()

            if stationarydistribution:
                self.GenerateStationaryDistribution()
            else:
                self.Instance.ForecastError = [forecasterror for p in self.Instance.ProductSet]
                self.Instance.RateOfKnownDemand = [
                    math.pow(rateknown, (t - self.Instance.NrTimeBucketWithoutUncertaintyBefore + 1))
                    for t in self.Instance.TimeBucketSet ]
                self.Instance.ForecastedAverageDemand = [[0.0 for p in self.Instance.ProductSet]
                                                         for t in self.Instance.TimeBucketSet]
                if longtimehorizon:
                    #get the average demand and the coefficient of variation
                    self.Instance.YearlyAverageDemand = [0 for p in self.Instance.ProductSet]
                    for p in range(len(finishproduct)):
                        prodindex = finishproduct[p]
                        self.Instance.YearlyAverageDemand[prodindex] = int(self.DTFile[0][p])

                    coefficientofvariation = float(self.Filename[3])/10.0

                    #generate the demand following a normal distribution and the coefficient of variation
                    self.Instance.ForecastedAverageDemand = [[ np.floor( np.random.normal(self.Instance.YearlyAverageDemand[p],
                                                                                         coefficientofvariation * self.Instance.YearlyAverageDemand[p], 1).clip( min=0.0)).tolist()[0]
                                                              if self.Instance.YearlyAverageDemand[p] > 0 and t >= self.Instance.NrTimeBucketWithoutUncertaintyBefore
                                                              else 0
                                                              for p in self.Instance.ProductSet]
                                                                for t in self.Instance.TimeBucketSet]
                    print  self.Instance.YearlyAverageDemand
                    print  coefficientofvariation
                    print  self.Instance.ForecastedAverageDemand
                else:
                    prodindex = 0
                    for p in range( len( finishproduct ) ):
                        prodindex = finishproduct[p]
                        timeindex = 0
                        stochastictime = range( self.Instance.NrTimeBucketWithoutUncertaintyBefore, self.Instance.NrTimeBucket - self.Instance.NrTimeBucketWithoutUncertaintyAfter)
                        for t in stochastictime:
                            timeindex += 1

                            if t <>  self.Instance.NrTimeBucketWithoutUncertaintyBefore + int(self.DTFile[timeindex][0]) - 1:
                                raise NameError( "Wrong time %d - %d -%d"%( t , int(self.DTFile[timeindex][0]) - 1 , timeindex ) )

                            self.Instance.ForecastedAverageDemand[t][prodindex] = float( self.DTFile[timeindex][p+1] )

                        for t in range( self.Instance.NrTimeBucket - self.Instance.NrTimeBucketWithoutUncertaintyAfter,  self.Instance.NrTimeBucket):
                            self.Instance.ForecastedAverageDemand[t][prodindex] = sum( self.Instance.ForecastedAverageDemand[t2][prodindex]
                                                                                       for t2 in stochastictime  ) / len(stochastictime)

                        self.Instance.YearlyAverageDemand = [sum(self.Instance.ForecastedAverageDemand[t][p]
                                                                 for t in self.Instance.TimeBucketSet
                                                                 if t >= self.Instance.NrTimeBucketWithoutUncertaintyBefore )
                                                             / (self.Instance.NrTimeBucket - self.Instance.NrTimeBucketWithoutUncertaintyBefore)
                                                             for p in self.Instance.ProductSet]

                self.Instance.ForcastedStandardDeviation = [ [ (1 - self.Instance.RateOfKnownDemand[t])
                                                               * self.Instance.ForecastError[p]
                                                               * self.Instance.ForecastedAverageDemand[t][p]
                                                               if t < (self.Instance.NrTimeBucket - self.Instance.NrTimeBucketWithoutUncertaintyAfter)
                                                               else 0.0
                                                               for p in self.Instance.ProductSet ]
                                                             for t in self.Instance.TimeBucketSet]

                self.Instance.YearlyStandardDevDemands = [sum(self.Instance.ForcastedStandardDeviation[t][p]
                                                 for t in self.Instance.TimeBucketSet) / self.Instance.NrTimeBucket
                                             for p in self.Instance.ProductSet]

    #This function generate the starting inventory
    def GenerateStartinInventory(self):
        self.Instance.StartingInventories = [  0.0 for p in self.Instance.ProductSet  ]

    def GenerateSetup(self, e="n"):

        TBO =  [  float( self.TBOFile [p ][1] ) for p in  self.Instance.ProductSet ]
        echlonstock = self.GetEchelonHoldingCost(e)

        finishproduct = []
        for p in self.Instance.ProductSet:
            if sum(1 for q in self.Instance.ProductSet if self.Instance.Requirements[q][p]) == 0:
                finishproduct.append(p)
        avgdemand =  [  0.0 for p in  self.Instance.ProductSet ]
        for p in range(len(finishproduct)):
           avgdemand[ finishproduct[p]] = float(self.Instance.YearlyAverageDemand[p ])

        for l in self.LevelSet:
            prodinlevel = [p for p in self.Instance.ProductSet if self.Level[p] == l]
            for p in prodinlevel:
                avgdemand[p] = sum(
                    avgdemand[q] * self.Instance.Requirements[q][p] for q in
                    self.Instance.ProductSet) + \
                               avgdemand[p]

        computedsetup = [ echlonstock[p]*avgdemand[p]*TBO[p]*TBO[p] / 2
                          for p in  self.Instance.ProductSet ]

        self.Instance.SetupCosts = [ 0 for p in self.Instance.ProductSet]
        startsetup = 3
        for p in self.Instance.ProductSet:
           self.Instance.SetupCosts[p] = sum( float( self.TMPFile[startsetup + p][i] ) for i in range( self.Instance.NrResource) )
           for i in range( self.Instance.NrResource):
               if float( self.TMPFile[startsetup + p][i] ) > 0 and float( self.TMPFile[startsetup + p][i] ) <> self.Instance.SetupCosts[p] \
                       or self.Instance.SetupCosts[p] <>  computedsetup[p]:
                   print "warning: The setup cost are not the same as the ones in the file!"
                  # raise NameError( "The setup cost are not read as expected" )

        if Constants.Debug:
            print "setupcost: %r"%self.Instance.SetupCosts
        self.Instance.SetupCosts = [ computedsetup[p ] for p in  self.Instance.ProductSet ]



    def GenerateCapacity(self, capacityfactor):

        startcapacity = 5 + 2 * self.Instance.NrProduct
        startsetup = 3
        self.Instance.Capacity = [ 0 for k in range(self.Instance.NrResource) ]
        for k in range(self.Instance.NrResource):
            self.Instance.Capacity[k] = float(self.TMPFile[startcapacity + k][0])

            #for i in range(self.Instance.NrTimeBucket - self.Instance.NrTimeBucketWithoutUncertaintyAfter - self.Instance.NrTimeBucketWithoutUncertaintyBefore ):
            #    if float(self.TMPFile[startcapacity + k][i]) <>  self.Instance.Capacity[k]:
            #        raise NameError("The capacities are not read as expected")

        if Constants.Debug:
            print "Capacity: %r" % self.Instance.Capacity

        self.Instance.ProcessingTime = [ [  float( self.DatFile[p +1  ][7] )
                                            if float(self.TMPFile[startsetup + p][k]) > 0
                                            else 0.0
                                            for k in range(self.Instance.NrResource)]
                                           for p in self.Instance.ProductSet]

        #As the average change, the capacity must change
        if ((self.Instance.Distribution == Constants.SlowMoving) \
             or (self.Instance.Distribution == Constants.Uniform) \
             or (self.Instance.Distribution == Constants.Binomial) ):
            for k in range(self.Instance.NrResource):
                self.ComputeAverageDependentDemand()
                self.Instance.Capacity[k] = math.ceil(float( sum( self.DependentAverageDemand[p] * self.Instance.ProcessingTime[p][k]
                                                        for p in self.Instance.ProductSet ) \
                                                   /  float(self.CapFile[k][1]) ) )


        if capacityfactor <> 0:
            for k in range(self.Instance.NrResource):
                self.ComputeAverageDependentDemand()
                self.Instance.Capacity[k] = math.ceil(float( sum( self.DependentAverageDemand[p] * self.Instance.ProcessingTime[p][k]
                                                        for p in self.Instance.ProductSet )* capacityfactor ) )
