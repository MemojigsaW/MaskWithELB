from app import webapp
import config
from flask import render_template, flash, url_for, redirect, request
import ELB_util


@webapp.route('/ELBV2Page', methods=['GET'])
def loadELBV2Page():
    ELBlist = []
    response = ELB_util.get_ELBV2()
    for ELB in response['LoadBalancers']:
        if (ELB['LoadBalancerArn'] == config.ELB_ARN) \
                and (ELB['DNSName'] == config.ELB_DNS) \
                and (config.ELB_SECURITY_GROUP in ELB['SecurityGroups']):
            ELBlist.append(ELB)

    listenerlist = []
    response = ELB_util.get_listeners()
    for listener in response['Listeners']:
        if (listener['LoadBalancerArn'] == config.ELB_ARN):
            listenerlist.append(listener)

    TargetGrouplist = []
    response = ELB_util.get_TargetGroup()
    for TG in response['TargetGroups']:
        if (TG['TargetGroupArn'] == config.TARGET_GROUP_ARN and
                (config.ELB_ARN in TG['LoadBalancerArns'])):
            TargetGrouplist.append(TG)

    TargetHealthlist = []
    response = ELB_util.get_TargetsHealth()
    for TH in response['TargetHealthDescriptions']:
        TargetHealthlist.append(TH)

    return render_template('ELBV2Page.html',
                           ELBDNS=config.ELB_DNS,
                           ELBARN=config.ELB_ARN,
                           TGARN=config.TARGET_GROUP_ARN,
                           ELB_dict_list=ELBlist,
                           listener_dict_list=listenerlist,
                           TG_dict_list=TargetGrouplist,
                           TH_dict_list=TargetHealthlist
                           )

@webapp.route('/api/reg_target', methods=['POST'])
def reg_target():
    instance = request.form.get("Instance_Id")
    response = ELB_util.reg_instance_to_TG(instance)
    flash(response, "ELBV2Page_error")
    return redirect(url_for('loadELBV2Page'))

@webapp.route('/api/dereg_target', methods=['POST'])
def dereg_target():
    instance = request.form.get("Instance_Id")
    response = ELB_util.dereg_instance_from_TG(instance)
    flash(response, "ELBV2Page_error")
    return redirect(url_for('loadELBV2Page'))