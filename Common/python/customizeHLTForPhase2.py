import FWCore.ParameterSet.Config as cms

from CondCore.CondDB.CondDB_cfi import CondDB as _CondDB

from JMETriggerAnalysis.Common.hltPhase2_L1T import customise_hltPhase2_L1T
from JMETriggerAnalysis.Common.hltPhase2_TRKv00 import customise_hltPhase2_TRKv00
from JMETriggerAnalysis.Common.hltPhase2_TRKv02 import customise_hltPhase2_TRKv02
from JMETriggerAnalysis.Common.hltPhase2_TRKv06 import customise_hltPhase2_TRKv06
from JMETriggerAnalysis.Common.hltPhase2_TRKv06p1 import customise_hltPhase2_TRKv06p1
from JMETriggerAnalysis.Common.hltPhase2_TRKv06p3 import customise_hltPhase2_TRKv06p3
from JMETriggerAnalysis.Common.hltPhase2_TRKv07p2 import customise_hltPhase2_TRKv07p2
from JMETriggerAnalysis.Common.hltPhase2_PF import customise_hltPhase2_PF
from JMETriggerAnalysis.Common.hltPhase2_JME import customise_hltPhase2_JME
from JMETriggerAnalysis.Common.multiplicityValueProducerFromNestedCollectionEdmNewDetSetVectorSiPixelClusterDouble_cfi\
 import multiplicityValueProducerFromNestedCollectionEdmNewDetSetVectorSiPixelClusterDouble as _nSiPixelClusters

from HLTrigger.Configuration.common import producers_by_type

from RecoHGCal.TICL.iterativeTICL_cff import injectTICLintoPF

def customise_hltPhase2_enableTICLInHGCalReconstruction(process):
    if not hasattr(process, 'iterTICLTask'):
       raise RuntimeError('process.iterTICLTask not found')

    # remove modules specific to SIM-assisted reconstruction
    del process.tpClusterProducer
    del process.quickTrackAssociatorByHits
    del process.simPFProducer

    process.iterTICLSequence = cms.Sequence(process.iterTICLTask)
    process.globalreco += process.iterTICLSequence
    process = injectTICLintoPF(process)

    return process

def customise_hltPhase2_disableMTDReconstruction(process):
    for _tmp1 in [
      'fastTimingLocalReco',
      'fastTimingLocalRecoTask',
      'fastTimingGlobalReco',
      'fastTimingGlobalRecoTask',
      'tofPIDSequence',
    ]:
      if hasattr(process, _tmp1):
        for _tmp2 in getattr(process, _tmp1).moduleNames():
          if hasattr(process, _tmp2):
            process.__delattr__(_tmp2)
        process.__delattr__(_tmp1)

    for _tmp in process.__dict__.keys():
      if ('Vertices4D' in _tmp) or ('Sorting4D' in _tmp):
        process.__delattr__(_tmp)

    # disable use of timing information in simPFProducer
    if hasattr(process, 'simPFProducer') and hasattr(process.simPFProducer, 'trackTimeValueMap'):
       del process.simPFProducer.trackTimeValueMap

    # remove MTD element from PFBlock inputs
    process.particleFlowBlock.elementImporters = [
      _tmp for _tmp in process.particleFlowBlock.elementImporters if _tmp.importerName != 'TrackTimingImporter'
    ]

    return process

def customise_hltPhase2_redefineReconstructionSequencesCommon(process):
    if not hasattr(process, 'reconstruction'):
       raise RuntimeError('reconstruction sequence process.reconstruction not found')

    # redefine input to fixedGridRhoFastjetAll
    # (in principle, this is not needed, since JESC modules are configured with 'fixedGridRhoFastjetAllTmp';
    #  nevertheless, this modification is applied, in order to make sure _particleFlowCands is consistently used)
    process.fixedGridRhoFastjetAll.pfCandidatesTag = 'particleFlowTmp'

    process.calolocalreco = cms.Sequence(
        process.ecalLocalRecoSequence
      + process.hcalLocalRecoSequence
    )

    process.localreco = cms.Sequence(
        process.bunchSpacingProducer
      + process.calolocalreco
      + process.muonlocalreco
      + process.trackerlocalreco
      + process.fastTimingLocalReco
    )

    # process.globalreco: reconstruction up to PFClusters
    if (not hasattr(process, 'globalreco_tracking')) and hasattr(process, 'globalreco_trackingTask'):
       process.globalreco_tracking = cms.Sequence(process.globalreco_trackingTask)

    process.tofPIDSequence = cms.Sequence(
        process.unsortedOfflinePrimaryVertices4DnoPID
      + process.tofPID4DnoPID
      + process.unsortedOfflinePrimaryVertices4D
      + process.tofPID
    )

    # remove PFElectron-related modules not needed for HLT-PF
    del process.particleFlowTmpPtrs

    _modulesToKeep = ['pfTrack']
    for _tmp1 in [
      'gedElectronPFIsolationDepositsTask',
      'gedGsfElectronTaskTmp',
      'particleFlowEGammaFinalTask',
      'particleFlowEGammaFullTask',
      'particleFlowTrackWithDisplacedVertexTask',
      'pfGsfElectronMVASelectionTask',
      'pfParticleSelectionTask',
    ]:
      if hasattr(process, _tmp1):
        for _tmp2 in getattr(process, _tmp1).moduleNames():
          if _tmp2 in _modulesToKeep: continue
          if hasattr(process, _tmp2):
            process.__delattr__(_tmp2)
        process.__delattr__(_tmp1)
    del _modulesToKeep

    # remove unnecessary modules related
    # to muon reconstruction
    for _tmp1 in [
      'muIsolationTask',
      'muonSelectionTypeTask',
    ]:
      if hasattr(process, _tmp1):
        for _tmp2 in getattr(process, _tmp1).moduleNames():
          if hasattr(process, _tmp2):
            process.__delattr__(_tmp2)
        process.__delattr__(_tmp1)

    process.globalreco = cms.Sequence(
        process.caloTowersRec
      + process.ecalClusters
#     + process.egammaGlobalReco
      + process.hcalGlobalRecoSequence

        # tracking
      + process.globalreco_tracking
      + process.standalonemuontracking # needs to be included for early muons of PF
      + process.hgcalLocalRecoSequence

        # timing
      + process.fastTimingGlobalReco # necessary for MTD inputs to PF
      + process.tofPIDSequence # contains tofPID maps

        # insert CaloJets sequence in process.globalreco
        # (module muons1stStep from muonGlobalReco requires AK4CaloJets [1])
      + process.hltAK4CaloJets # was: process.jetGlobalReco

      + process.muonGlobalReco
#     + process.muoncosmicreco
      + process.particleFlowCluster
#     + process.pfTrackingGlobalReco
    )

    if hasattr(process, 'hltAK4CaloJets'):
       process.globalreco += process.hltAK4CaloJets
       # modify CaloJets input to muons1stStep
       process.muons1stStep.JetExtractorPSet.JetCollectionLabel = 'hltAK4CaloJets'
    else:
       process.globalreco += process.jetGlobalReco

    process.highlevelreco = cms.Sequence(
        process.particleFlowReco
    )

    process.reconstruction = cms.Sequence(
        process.localreco
      + process.globalreco
      + process.highlevelreco
    )

    return process

def customise_hltPhase2_common(process):
    # ES modules for Jet Energy Scale Corrections
    process.jescESSource = cms.ESSource('PoolDBESSource',
      _CondDB.clone(connect = 'sqlite_file:/afs/cern.ch/work/m/missirol/public/phase2/JESC/Phase2HLTTDR_V5_MC/Phase2HLTTDR_V5_MC.db'),
      toGet = cms.VPSet(
        cms.PSet(
          record = cms.string('JetCorrectionsRecord'),
          tag = cms.string('JetCorrectorParametersCollection_Phase2HLTTDR_V5_MC_AK4PFPuppiHLT'),
          label = cms.untracked.string('AK4PFPuppiHLT')
        ),
        cms.PSet(
          record = cms.string('JetCorrectionsRecord'),
          tag = cms.string('JetCorrectorParametersCollection_Phase2HLTTDR_V5_MC_AK8PFPuppiHLT'),
          label = cms.untracked.string('AK8PFPuppiHLT')
        ),
      ),
    )
    process.jescESPrefer = cms.ESPrefer('PoolDBESSource', 'jescESSource')

    # prevent access to inputs from RECO step (if available),
    # except for Offline objects to be used saved in the NTuple,
    # or used for validation purposes
    process.source.dropDescendantsOfDroppedBranches = cms.untracked.bool(False)

    process.source.inputCommands = cms.untracked.vstring([
      'keep *_*_*_*',
      'drop *_*_*_RECO',

      # L1T
      'keep *_L1TkPrimaryVertex__RECO',
      'keep *_l1pfCandidates_Puppi_RECO',
      'keep *_ak4PFL1Calo__RECO',
      'keep *_ak4PFL1CaloCorrected__RECO',
      'keep *_ak4PFL1PF__RECO',
      'keep *_ak4PFL1PFCorrected__RECO',
      'keep *_ak4PFL1Puppi__RECO',
      'keep *_ak4PFL1PuppiCorrected__RECO',
      'keep *_l1PFMetCalo__RECO',
      'keep *_l1PFMetPF__RECO',
      'keep *_l1PFMetPuppi__RECO',

      # Offline
      'keep *_fixedGridRhoFastjetAll__RECO',
      'keep *_offlineSlimmedPrimaryVertices__RECO',
      'keep *_packedPFCandidates__RECO',
      'keep *_slimmedMuons__RECO',
      'keep *_slimmedJets__RECO',
      'keep *_slimmedJetsPuppi__RECO',
      'keep *_slimmedJetsAK8*_*_RECO',
      'keep *_slimmedMETs__RECO',
      'keep *_slimmedMETsPuppi__RECO',
    ])

    return process

def customise_hltPhase2_redefineReconstructionSequences(process, useL1T=True, TRK='v06p1', useTICL=True, useMTD=False):
    # reset schedule
    process.setSchedule_(cms.Schedule())

    if useL1T:
       process = customise_hltPhase2_L1T(process)

    _trkCustomFuncDict = {
      'v00'  : customise_hltPhase2_TRKv00,
      'v02'  : customise_hltPhase2_TRKv02,
      'v06'  : customise_hltPhase2_TRKv06,
      'v06p1': customise_hltPhase2_TRKv06p1,
      'v06p3': customise_hltPhase2_TRKv06p3,
      'v07p2': customise_hltPhase2_TRKv07p2,
    }
    process = _trkCustomFuncDict[TRK](process)

    process = customise_hltPhase2_PF(process)
    process = customise_hltPhase2_JME(process)
    process = customise_hltPhase2_redefineReconstructionSequencesCommon(process)

    if not useMTD:
       process = customise_hltPhase2_disableMTDReconstruction(process)

    if useTICL:
       process = customise_hltPhase2_enableTICLInHGCalReconstruction(process)

    process = customise_hltPhase2_common(process)

    return process

def customise_hltPhase2_scheduleHLTJMERecoWithoutFilters(process):
    process.HLTJMESequence = cms.Sequence(
        process.HLTCaloMETReconstruction
#     + process.HLTCaloJetsReconstruction
      + process.HLTPFClusterJMEReconstruction
      + process.HLTAK4PFJetsReconstruction
      + process.HLTAK8PFJetsReconstruction
      + process.HLTPFJetsCHSReconstruction
      + process.HLTPFMETsReconstruction
      + process.HLTPFCHSMETReconstruction
      + process.HLTPFSoftKillerMETReconstruction
      + process.HLTPFPuppiJMEReconstruction
    )

    process.reconstruction += process.HLTJMESequence

    process.p = cms.Path(process.RawToDigi + process.reconstruction)

    # schedule
    process.schedule_().append(process.p)

    return process

def customise_hltPhase2_scheduleJMETriggers(process):
    ## sequence: HLT-JME objects (without filters)
    ## (kept for now to study object performance without preselections)
    process.HLTJMESequence = cms.Sequence(
        process.HLTCaloMETReconstruction
#     + process.HLTCaloJetsReconstruction
      + process.HLTPFClusterJMEReconstruction
      + process.HLTAK4PFJetsReconstruction
      + process.HLTAK8PFJetsReconstruction
      + process.HLTPFJetsCHSReconstruction
      + process.HLTPFMETsReconstruction
      + process.HLTPFCHSMETReconstruction
      + process.HLTPFSoftKillerMETReconstruction
      + process.HLTPFPuppiJMEReconstruction
    )

    ## sequence: ParticleFlow
    process.HLTParticleFlowSequence = cms.Sequence(
        process.RawToDigi
      + process.localreco
      + process.globalreco
      + process.highlevelreco
    )

    ## sequence: AK4 Jets, PFCHS
    process.HLTParticleFlowCHSSequence = cms.Sequence(
        process.HLTParticleFlowSequence
      + process.particleFlowPtrs
      + process.goodOfflinePrimaryVertices
      + process.pfPileUpJME
      + process.pfNoPileUpJME
    )

    process.HLTAK4PFCHSJetsReconstruction = cms.Sequence(
        process.hltAK4PFCHSJets
      + process.hltAK4PFCHSJetCorrectorL1
      + process.hltAK4PFCHSJetCorrectorL2
      + process.hltAK4PFCHSJetCorrectorL3
      + process.hltAK4PFCHSJetCorrector
      + process.hltAK4PFCHSJetsCorrected
    )

#    ## sequence: AK8 Jets, PFCHS
#    process.HLTAK8PFCHSJetsReconstruction = cms.Sequence(
#        process.hltAK8PFCHSJets
#      + process.hltAK8PFCHSJetCorrectorL1
#      + process.hltAK8PFCHSJetCorrectorL2
#      + process.hltAK8PFCHSJetCorrectorL3
#      + process.hltAK8PFCHSJetCorrector
#      + process.hltAK8PFCHSJetsCorrected
#    )

    ## sequence: AK4 Jets, PFPuppi
    process.HLTAK4PFPuppiJetsReconstruction = cms.Sequence(
        process.goodOfflinePrimaryVertices
      + process.hltPFPuppi
      + process.hltAK4PFPuppiJets
      + process.hltAK4PFPuppiJetCorrectorL1
      + process.hltAK4PFPuppiJetCorrectorL2
      + process.hltAK4PFPuppiJetCorrectorL3
      + process.hltAK4PFPuppiJetCorrector
      + process.hltAK4PFPuppiJetsCorrected
    )

#    ## sequence: AK8 Jets, PFPuppi
#    process.HLTAK8PFPuppiJetsReconstruction = cms.Sequence(
#        process.goodOfflinePrimaryVertices
#      + process.hltPFPuppi
#      + process.hltAK8PFPuppiJets
#      + process.hltAK8PFPuppiJetCorrectorL2
#      + process.hltAK8PFPuppiJetCorrectorL3
#      + process.hltAK8PFPuppiJetCorrector
#      + process.hltAK8PFPuppiJetsCorrected
#    )

    ## sequence: PFPuppi MET (Raw)
    process.HLTPFPuppiMETReconstruction = cms.Sequence(
        process.goodOfflinePrimaryVertices
      + process.hltPFPuppiNoLep
      + process.hltPFPuppiMET
    )

    ## Single-Jet producers+filters
    process.l1tSinglePFPuppiJet200off = cms.EDFilter('L1TJetFilter',
      inputTag = cms.InputTag('l1tSlwPFPuppiJetsCorrected', 'Phase1L1TJetFromPfCandidates'),
      Scalings = cms.PSet(
        barrel = cms.vdouble(11.1254, 1.40627, 0),
        overlap = cms.vdouble(24.8375, 1.4152, 0),
        endcap = cms.vdouble(42.4039, 1.33052, 0),
      ),
      MinPt = cms.double(200.),
      MinEta = cms.double(-5.),
      MaxEta = cms.double(5.),
      MinN = cms.int32(1),
    )

    _hltSinglePFJet100 = cms.EDFilter('HLT1PFJet',
      MaxEta = cms.double(5.0),
      MaxMass = cms.double(-1.0),
      MinE = cms.double(-1.0),
      MinEta = cms.double(-1.0),
      MinMass = cms.double(-1.0),
      MinN = cms.int32(1),
      MinPt = cms.double(100.0),
      inputTag = cms.InputTag(''),
      saveTags = cms.bool(True),
      triggerType = cms.int32(85),
    )

    process.hltSingleAK4PFJet550 = _hltSinglePFJet100.clone(inputTag = 'hltAK4PFJetsCorrected', MinPt = 550., MaxEta = 5.)
    process.hltSingleAK4PFCHSJet550 = _hltSinglePFJet100.clone(inputTag = 'hltAK4PFCHSJetsCorrected', MinPt = 550., MaxEta = 5.)
    process.hltSingleAK4PFPuppiJet550 = _hltSinglePFJet100.clone(inputTag = 'hltAK4PFPuppiJetsCorrected', MinPt = 550., MaxEta = 5.)

    ## HT/MHT producers+filters

    # L1T-HT
    process.l1tPFPuppiHT = cms.EDProducer('HLTHtMhtProducer',
      jetsLabel = cms.InputTag('l1tSlwPFPuppiJetsCorrected', 'Phase1L1TJetFromPfCandidates'),
      minPtJetHt = cms.double(30.),
      maxEtaJetHt = cms.double(2.4),
    )

    process.l1tPFPuppiHT450off = cms.EDFilter('L1TEnergySumFilter',
      inputTag = cms.InputTag('l1tPFPuppiHT'),
      Scalings = cms.PSet(
        theScalings = cms.vdouble(50.0182, 1.0961, 0), # PFPhase1HT090OfflineEtCut
      ),
      TypeOfSum = cms.string('HT'),
      MinPt = cms.double(450.),
    )

    # HLT-HT/MHT
    _hltHtMht = cms.EDProducer('HLTHtMhtProducer',
      excludePFMuons = cms.bool(False),
      jetsLabel = cms.InputTag(''),
      maxEtaJetHt = cms.double(5.0),
      maxEtaJetMht = cms.double(999.0),
      minNJetHt = cms.int32(0),
      minNJetMht = cms.int32(0),
      minPtJetHt = cms.double(30.0),
      minPtJetMht = cms.double(0.0),
      pfCandidatesLabel = cms.InputTag(''),
      usePt = cms.bool(True)
    )

    _hltHT100 = cms.EDFilter('HLTHtMhtFilter',
      htLabels = cms.VInputTag(''),
      meffSlope = cms.vdouble(1.0),
      mhtLabels = cms.VInputTag(''),
      minHt = cms.vdouble(100.0),
      minMeff = cms.vdouble(0.0),
      minMht = cms.vdouble(0.0),
      saveTags = cms.bool(True)
    )

    _hltMHT100 = cms.EDFilter('HLTMhtFilter',
      mhtLabels = cms.VInputTag(''),
      minMht = cms.vdouble(100.0),
      saveTags = cms.bool(True)
    )

    process.hltPFPuppiHT = _hltHtMht.clone(jetsLabel = 'hltAK4PFPuppiJetsCorrected', minPtJetHt = 30., maxEtaJetHt = 2.4, minPtJetMht = 30., maxEtaJetMht = 2.4)
    process.hltPFPuppiHT60 = _hltHT100.clone(htLabels = ['hltPFPuppiHT'], mhtLabels = ['hltPFPuppiHT'], minHt = [60.])
    process.hltPFPuppiHT1050 = _hltHT100.clone(htLabels = ['hltPFPuppiHT'], mhtLabels = ['hltPFPuppiHT'], minHt = [1050.])

    process.hltPFPuppiMHT = _hltHtMht.clone(jetsLabel = 'hltAK4PFPuppiJetsCorrected', minPtJetHt = 30., maxEtaJetHt = 5.0, minPtJetMht = 30., maxEtaJetMht = 5.0, usePt = False)
    process.hltPFPuppiMHT120 = _hltMHT100.clone(mhtLabels = ['hltPFPuppiMHT'], minMht = [120.])

    ## MET producers+filters
    process.l1tPFPuppiMET200off = cms.EDFilter('L1TPFEnergySumFilter',
      inputTag = cms.InputTag('l1PFMetPuppi'),
      Scalings = cms.PSet(
        theScalings = cms.vdouble(54.2859, 1.39739, 0), # PuppiMET090OfflineEtCut
      ),
      TypeOfSum = cms.string('MET'),
      MinPt = cms.double(200.),
    )

    process.l1tPFPuppiMET245off = process.l1tPFPuppiMET200off.clone(MinPt = 245.)

    _hltPFMET200 = cms.EDFilter('HLT1PFMET',
      MaxEta = cms.double(-1.0),
      MaxMass = cms.double(-1.0),
      MinE = cms.double(-1.0),
      MinEta = cms.double(-1.0),
      MinMass = cms.double(-1.0),
      MinN = cms.int32(1),
      MinPt = cms.double(200.0),
      inputTag = cms.InputTag(''),
      saveTags = cms.bool(True),
      triggerType = cms.int32(87),
    )

    process.hltPFMET250 = _hltPFMET200.clone(inputTag = 'hltPFMET', MinPt = 250.)
    process.hltPFCHSMET250 = _hltPFMET200.clone(inputTag = 'hltPFCHSMET', MinPt = 250.)
    process.hltPFPuppiMET250 = _hltPFMET200.clone(inputTag = 'hltPFPuppiMET', MinPt = 250.)

    process.hltPFPuppiMET120 = _hltPFMET200.clone(inputTag = 'hltPFPuppiMET', MinPt = 120.)

    ## Trigger Paths
    process.MC_JME = cms.Path(
        process.HLTParticleFlowSequence
      + process.HLTJMESequence
      + process.hltPFPuppiHT
      + process.hltPFPuppiMHT
    )

    process.L1T_SinglePFPuppiJet200off = cms.Path(
        process.l1tSinglePFPuppiJet200off
    )

    process.HLT_AK4PFJet550 = cms.Path(
        process.l1tSinglePFPuppiJet200off
      + process.HLTParticleFlowSequence
      + process.HLTAK4PFJetsReconstruction
      + process.hltSingleAK4PFJet550
    )

    process.HLT_AK4PFCHSJet550 = cms.Path(
        process.l1tSinglePFPuppiJet200off
      + process.HLTParticleFlowCHSSequence
      + process.HLTAK4PFCHSJetsReconstruction
      + process.hltSingleAK4PFCHSJet550
    )

    process.HLT_AK4PFPuppiJet550 = cms.Path(
        process.l1tSinglePFPuppiJet200off
      + process.HLTParticleFlowSequence
      + process.HLTAK4PFPuppiJetsReconstruction
      + process.hltSingleAK4PFPuppiJet550
    )

    process.L1T_PFPuppiHT450off = cms.Path(
        process.l1tPFPuppiHT
      + process.l1tPFPuppiHT450off
    )

    process.HLT_PFPuppiHT1050 = cms.Path(
        process.l1tPFPuppiHT
      + process.l1tPFPuppiHT450off
      + process.HLTParticleFlowSequence
      + process.HLTAK4PFPuppiJetsReconstruction
      + process.hltPFPuppiHT
      + process.hltPFPuppiHT1050
    )

    process.L1T_PFPuppiMET200off = cms.Path(
        process.l1tPFPuppiMET200off
    )

    process.L1T_PFPuppiMET245off = cms.Path(
        process.l1tPFPuppiMET245off
    )

    process.HLT_PFMET250 = cms.Path(
        process.l1tPFPuppiMET200off
      + process.HLTParticleFlowSequence
      + process.hltPFMET
      + process.hltPFMET250
    )

    process.HLT_PFCHSMET250 = cms.Path(
        process.l1tPFPuppiMET200off
      + process.HLTParticleFlowCHSSequence
      + process.HLTPFCHSMETReconstruction
      + process.hltPFCHSMET250
    )

    process.HLT_PFPuppiMET250 = cms.Path(
        process.l1tPFPuppiMET200off
      + process.HLTParticleFlowSequence
      + process.HLTPFPuppiMETReconstruction
      + process.hltPFPuppiMET250
    )

    process.HLT_PFPuppiMET120 = cms.Path(
        process.l1tPFPuppiMET200off
      + process.HLTParticleFlowSequence
      + process.HLTPFPuppiMETReconstruction
      + process.hltPFPuppiMET120
    )

    process.HLT_PFPuppiMET120_PFPuppiMHT120 = cms.Path(
        process.l1tPFPuppiMET200off
      + process.HLTParticleFlowSequence
      + process.HLTPFPuppiMETReconstruction
      + process.hltPFPuppiMET120
      + process.HLTAK4PFPuppiJetsReconstruction
      + process.hltPFPuppiMHT
      + process.hltPFPuppiMHT120
    )

    process.HLT_PFPuppiMET120_PFPuppiMHT120_PFPuppiHT60 = cms.Path(
        process.l1tPFPuppiMET200off
      + process.HLTParticleFlowSequence
      + process.HLTPFPuppiMETReconstruction
      + process.hltPFPuppiMET120
      + process.HLTAK4PFPuppiJetsReconstruction
      + process.hltPFPuppiMHT
      + process.hltPFPuppiMHT120
      + process.hltPFPuppiHT
      + process.hltPFPuppiHT60
    )

    # schedule
    process.schedule_().extend([
      process.MC_JME,

      process.L1T_SinglePFPuppiJet200off,
      process.HLT_AK4PFJet550,
      process.HLT_AK4PFCHSJet550,
      process.HLT_AK4PFPuppiJet550,

      process.L1T_PFPuppiHT450off,
      process.HLT_PFPuppiHT1050,

      process.L1T_PFPuppiMET200off,
      process.L1T_PFPuppiMET245off,
      process.HLT_PFMET250,
      process.HLT_PFCHSMET250,
      process.HLT_PFPuppiMET250,

      process.HLT_PFPuppiMET120,
      process.HLT_PFPuppiMET120_PFPuppiMHT120,
      process.HLT_PFPuppiMET120_PFPuppiMHT120_PFPuppiHT60,
    ])

    return process

def customise_hltPhase2_reconfigurePuppi(process, TICL):
    process.hltPixelClustersMultiplicity = _nSiPixelClusters.clone(src = 'siPixelClusters', defaultValue = -1.)

    for mod_i in producers_by_type(process, 'PuppiProducer'):
      for seqName_i in process.sequences_():
        seq_i = getattr(process, seqName_i)
        if not seq_i.contains(process.pixelTracks):
          seq_i._replaceIfHeldDirectly(mod_i, process.hltPixelClustersMultiplicity + mod_i)

      mod_i.usePUProxyValue = True
      mod_i.PUProxyValue = 'hltPixelClustersMultiplicity'
      for algo_idx in range(len(mod_i.algos)):
        if len(mod_i.algos[algo_idx].MinNeutralPt) != len(mod_i.algos[algo_idx].MinNeutralPtSlope):
          raise RuntimeError('instance of PuppiProducer is misconfigured:\n\n'+str(mod_i)+' = '+mod_i.dumpPython())

        for algoReg_idx in range(len(mod_i.algos[algo_idx].MinNeutralPt)):
          mod_i.algos[algo_idx].MinNeutralPt[algoReg_idx] += 20.7 * mod_i.algos[algo_idx].MinNeutralPtSlope[algoReg_idx]
          mod_i.algos[algo_idx].MinNeutralPtSlope[algoReg_idx] *= 0.000634

      if TICL:
        mod_i.algos[0].etaMin = [-0.01, 1.5, 2.5, 2.8, 3.2]
        mod_i.algos[0].etaMax = [1.5, 2.5, 2.8, 3.2, 3.5]
        mod_i.algos[0].ptMin = [mod_i.algos[0].ptMin[0]] + 4*[mod_i.algos[0].ptMin[1]]
        mod_i.algos[0].MinNeutralPt = [mod_i.algos[0].MinNeutralPt[0]] + 4*[mod_i.algos[0].MinNeutralPt[1]]
        mod_i.algos[0].MinNeutralPtSlope = [mod_i.algos[0].MinNeutralPtSlope[0]] + 4*[mod_i.algos[0].MinNeutralPtSlope[1]]
        mod_i.algos[0].PtMaxNeutrals = [mod_i.algos[0].PtMaxNeutrals[0]] + 4*[mod_i.algos[0].PtMaxNeutrals[1]]#!!
        mod_i.algos[0].PtMaxNeutralsStartSlope = [mod_i.algos[0].PtMaxNeutralsStartSlope[0]] + 4*[mod_i.algos[0].PtMaxNeutralsStartSlope[1]]#!!
        mod_i.algos[0].RMSEtaSF = [mod_i.algos[0].RMSEtaSF[0]] + 4*[mod_i.algos[0].RMSEtaSF[1]]
        mod_i.algos[0].MedEtaSF = [mod_i.algos[0].MedEtaSF[0]] + 4*[mod_i.algos[0].MedEtaSF[1]]

        mod_i.algos[0].MinNeutralPt[1] += 1.
        mod_i.algos[0].MinNeutralPt[3] += 1.
        mod_i.algos[0].MinNeutralPtSlope[3] *= 4.
        mod_i.algos[0].PtMaxNeutrals[3] = -1.

    return process

def customise_hltPhase2_scheduleHLTJMERecoWithoutFilters_TRKv00(process):
    process = customise_hltPhase2_redefineReconstructionSequences(process, TRK='v00', useTICL=False)
    process = customise_hltPhase2_scheduleHLTJMERecoWithoutFilters(process)
    return process

def customise_hltPhase2_scheduleHLTJMERecoWithoutFilters_TRKv00_TICL(process):
    process = customise_hltPhase2_redefineReconstructionSequences(process, TRK='v00', useTICL=True)
    process = customise_hltPhase2_scheduleHLTJMERecoWithoutFilters(process)
    return process

def customise_hltPhase2_scheduleHLTJMERecoWithoutFilters_TRKv02(process):
    process = customise_hltPhase2_redefineReconstructionSequences(process, TRK='v02', useTICL=False)
    process = customise_hltPhase2_scheduleHLTJMERecoWithoutFilters(process)
    process = customise_hltPhase2_reconfigurePuppi(process, TICL=False)
    return process

def customise_hltPhase2_scheduleHLTJMERecoWithoutFilters_TRKv02_TICL(process):
    process = customise_hltPhase2_redefineReconstructionSequences(process, TRK='v02', useTICL=True)
    process = customise_hltPhase2_scheduleHLTJMERecoWithoutFilters(process)
    process = customise_hltPhase2_reconfigurePuppi(process, TICL=True)
    return process

def customise_hltPhase2_scheduleHLTJMERecoWithoutFilters_TRKv06(process):
    process = customise_hltPhase2_redefineReconstructionSequences(process, TRK='v06', useTICL=False)
    process = customise_hltPhase2_scheduleHLTJMERecoWithoutFilters(process)
    process = customise_hltPhase2_reconfigurePuppi(process, TICL=False)
    return process

def customise_hltPhase2_scheduleHLTJMERecoWithoutFilters_TRKv06_TICL(process):
    process = customise_hltPhase2_redefineReconstructionSequences(process, TRK='v06', useTICL=True)
    process = customise_hltPhase2_scheduleHLTJMERecoWithoutFilters(process)
    process = customise_hltPhase2_reconfigurePuppi(process, TICL=True)
    return process

def customise_hltPhase2_scheduleHLTJMERecoWithoutFilters_TRKv06p1(process):
    process = customise_hltPhase2_redefineReconstructionSequences(process, TRK='v06p1', useTICL=False)
    process = customise_hltPhase2_scheduleHLTJMERecoWithoutFilters(process)
    process = customise_hltPhase2_reconfigurePuppi(process, TICL=False)
    return process

def customise_hltPhase2_scheduleHLTJMERecoWithoutFilters_TRKv06p1_TICL(process):
    process = customise_hltPhase2_redefineReconstructionSequences(process, TRK='v06p1', useTICL=True)
    process = customise_hltPhase2_scheduleHLTJMERecoWithoutFilters(process)
    process = customise_hltPhase2_reconfigurePuppi(process, TICL=True)
    return process

def customise_hltPhase2_scheduleHLTJMERecoWithoutFilters_TRKv06p3(process):
    process = customise_hltPhase2_redefineReconstructionSequences(process, TRK='v06p3', useTICL=False)
    process = customise_hltPhase2_scheduleHLTJMERecoWithoutFilters(process)
    process = customise_hltPhase2_reconfigurePuppi(process, TICL=False)
    return process

def customise_hltPhase2_scheduleHLTJMERecoWithoutFilters_TRKv06p3_TICL(process):
    process = customise_hltPhase2_redefineReconstructionSequences(process, TRK='v06p3', useTICL=True)
    process = customise_hltPhase2_scheduleHLTJMERecoWithoutFilters(process)
    process = customise_hltPhase2_reconfigurePuppi(process, TICL=True)
    return process

def customise_hltPhase2_scheduleHLTJMERecoWithoutFilters_TRKv07p2(process):
    process = customise_hltPhase2_redefineReconstructionSequences(process, TRK='v07p2', useTICL=False)
    process = customise_hltPhase2_scheduleHLTJMERecoWithoutFilters(process)
    process = customise_hltPhase2_reconfigurePuppi(process, TICL=False)
    return process

def customise_hltPhase2_scheduleHLTJMERecoWithoutFilters_TRKv07p2_TICL(process):
    process = customise_hltPhase2_redefineReconstructionSequences(process, TRK='v07p2', useTICL=True)
    process = customise_hltPhase2_scheduleHLTJMERecoWithoutFilters(process)
    process = customise_hltPhase2_reconfigurePuppi(process, TICL=True)
    return process

def customise_hltPhase2_scheduleJMETriggers_TRKv00(process):
    process = customise_hltPhase2_redefineReconstructionSequences(process, TRK='v00', useTICL=False)
    process = customise_hltPhase2_scheduleJMETriggers(process)
    return process

def customise_hltPhase2_scheduleJMETriggers_TRKv00_TICL(process):
    process = customise_hltPhase2_redefineReconstructionSequences(process, TRK='v00', useTICL=True)
    process = customise_hltPhase2_scheduleJMETriggers(process)
    return process

def customise_hltPhase2_scheduleJMETriggers_TRKv02(process):
    process = customise_hltPhase2_redefineReconstructionSequences(process, TRK='v02', useTICL=False)
    process = customise_hltPhase2_scheduleJMETriggers(process)
    process = customise_hltPhase2_reconfigurePuppi(process, TICL=False)
    return process

def customise_hltPhase2_scheduleJMETriggers_TRKv02_TICL(process):
    process = customise_hltPhase2_redefineReconstructionSequences(process, TRK='v02', useTICL=True)
    process = customise_hltPhase2_scheduleJMETriggers(process)
    process = customise_hltPhase2_reconfigurePuppi(process, TICL=True)
    return process

def customise_hltPhase2_scheduleJMETriggers_TRKv06(process):
    process = customise_hltPhase2_redefineReconstructionSequences(process, TRK='v06', useTICL=False)
    process = customise_hltPhase2_scheduleJMETriggers(process)
    process = customise_hltPhase2_reconfigurePuppi(process, TICL=False)
    return process

def customise_hltPhase2_scheduleJMETriggers_TRKv06_TICL(process):
    process = customise_hltPhase2_redefineReconstructionSequences(process, TRK='v06', useTICL=True)
    process = customise_hltPhase2_scheduleJMETriggers(process)
    process = customise_hltPhase2_reconfigurePuppi(process, TICL=True)
    return process

def customise_hltPhase2_scheduleJMETriggers_TRKv06p1(process):
    process = customise_hltPhase2_redefineReconstructionSequences(process, TRK='v06p1', useTICL=False)
    process = customise_hltPhase2_scheduleJMETriggers(process)
    process = customise_hltPhase2_reconfigurePuppi(process, TICL=False)
    return process

def customise_hltPhase2_scheduleJMETriggers_TRKv06p1_TICL(process):
    process = customise_hltPhase2_redefineReconstructionSequences(process, TRK='v06p1', useTICL=True)
    process = customise_hltPhase2_scheduleJMETriggers(process)
    process = customise_hltPhase2_reconfigurePuppi(process, TICL=True)
    return process

def customise_hltPhase2_scheduleJMETriggers_TRKv06p3(process):
    process = customise_hltPhase2_redefineReconstructionSequences(process, TRK='v06p3', useTICL=False)
    process = customise_hltPhase2_scheduleJMETriggers(process)
    process = customise_hltPhase2_reconfigurePuppi(process, TICL=False)
    return process

def customise_hltPhase2_scheduleJMETriggers_TRKv06p3_TICL(process):
    process = customise_hltPhase2_redefineReconstructionSequences(process, TRK='v06p3', useTICL=True)
    process = customise_hltPhase2_scheduleJMETriggers(process)
    process = customise_hltPhase2_reconfigurePuppi(process, TICL=True)
    return process

def customise_hltPhase2_scheduleJMETriggers_TRKv07p2(process):
    process = customise_hltPhase2_redefineReconstructionSequences(process, TRK='v07p2', useTICL=False)
    process = customise_hltPhase2_scheduleJMETriggers(process)
    process = customise_hltPhase2_reconfigurePuppi(process, TICL=False)
    return process

def customise_hltPhase2_scheduleJMETriggers_TRKv07p2_TICL(process):
    process = customise_hltPhase2_redefineReconstructionSequences(process, TRK='v07p2', useTICL=True)
    process = customise_hltPhase2_scheduleJMETriggers(process)
    process = customise_hltPhase2_reconfigurePuppi(process, TICL=True)
    return process
