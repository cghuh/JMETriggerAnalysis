from WMCore.Configuration import Configuration

store_dir = 'jme_trigger/jmeTriggerNtuples/Phase2/v2/191029'
sample_name = 'QCD_Pt_0_1000_14TeV_PU200'

MIN_DSET = '/QCD_Pt_0_1000_14TeV_TuneCUETP8M1/PhaseIITDRSpring19MiniAOD-PU200_106X_upgrade2023_realistic_v3-v2/MINIAODSIM'
RAW_DSET = '/QCD_Pt_0_1000_14TeV_TuneCUETP8M1/PhaseIITDRSpring19DR-PU200_106X_upgrade2023_realistic_v3-v2/GEN-SIM-DIGI-RAW'

config = Configuration()

config.section_('General')
config.General.requestName = 'jmeTriggerNTuple_'+sample_name
config.General.transferOutputs = True
config.General.transferLogs = True

config.section_('JobType')
config.JobType.pluginName  = 'Analysis'
config.JobType.maxMemoryMB = 5000
config.JobType.psetName = 'jmeTriggerNTuple_step3_CHSPFJets_11_0_0_pre7_cfg.py'
config.JobType.inputFiles = ['step3_CHSPFJets_11_0_0_pre7.py']
config.JobType.pyCfgParams = ['output='+sample_name+'.root']
config.JobType.maxJobRuntimeMin = 2500
#config.JobType.numCores = 4

config.section_('Data')
config.Data.publication = False
config.Data.ignoreLocality = False
config.Data.splitting = 'EventAwareLumiBased'
config.Data.inputDataset = MIN_DSET
config.Data.secondaryInputDataset = RAW_DSET
config.Data.outLFNDirBase = '/store/user/missirol/'+store_dir+'/'+sample_name
config.Data.unitsPerJob = 100
config.Data.totalUnits = -1

config.section_('Site')
config.Site.storageSite = 'T2_DE_DESY'
if config.Data.ignoreLocality:
   config.Site.whitelist = ['T2_CH_CERN', 'T2_DE_*']

config.section_('User')