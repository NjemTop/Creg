import requests
import re

login = "$(svc_login)"
pswd = "$(svc_pswd)"
back_full = "$(Build.SourceBranch)".removeprefix("refs/heads/")
external_front = "" + "$(front_feat_name)"
external_back = "" + "$(back_feat_name)"
external_feat_number = "" + "$(feat_number)"

def calc_bm_branches():
    front_list = []
    try:
        response = requests.get(
            'https://tfs03.boardmaps.ru/DefaultCollection/BoardMapsScrum/_apis/git/repositories/klever/refs',
            auth=(login, pswd)
        )
        response.raise_for_status()
        data = response.json()
        for i in range(len(data['value'])):
            front_list.append(data['value'][i]['name'])
    except requests.exceptions.RequestException as e:
        print(f"Error fetching branches: {e}")
        raise
    
    if external_front != "":
        front = external_front
        back = external_back
        feature_number = external_feat_number
        return front, back, feature_number
    else:
        back_matches = re.findall(r'\d+', back_full)
        if not back_matches:
            raise ValueError(f"No digits found in back_full: {back_full}")
        back = back_matches[0]
        for n in range(len(front_list)):
            try:
                front = re.findall(r'\d+', front_list[n])[0]
            except IndexError:
                front = None
            if front == back:
                front = front_list[n].removeprefix("refs/heads/")
                back = back_full
                feature_number = re.findall(r'\d+', back_full)[0]
                return front, back, feature_number
        front = "dev"
        back = back_full
        feature_number = re.findall(r'\d+', back_full)[0]
        return front, back, feature_number

def calc_helm_branch(feat):
    helm_list = []
    feature_number = feat
    try:
        response = requests.get(
            'https://tfs03.boardmaps.ru/DefaultCollection/BoardMapsScrum/_apis/git/repositories/helm/refs',
            auth=(login, pswd)
        )
        response.raise_for_status()
        data = response.json()
        for i in range(len(data['value'])):
            helm_list.append(data['value'][i]['name'])
    except requests.exceptions.RequestException as e:
        print(f"Error fetching helm branches: {e}")
        raise
    
    for n in range(len(helm_list)):
        try:
            helm_feat = re.findall(r'\d+', helm_list[n])[0]
        except IndexError:
            helm_feat = None
        if feature_number == helm_feat:
            helm_branch = helm_list[n].removeprefix("refs/heads/")
            return helm_branch
        else:
            helm_branch = "dev"
    return helm_branch

try:
    front, back, feature_number = calc_bm_branches()
    helm = calc_helm_branch(feature_number)
    print(f"front_branch: {front}\nback_branch: {back}\nfeature_number: {feature_number}\nhelm_branch: {helm}")

    print(f'##vso[task.setvariable variable=FrontBranch]{front}')
    print(f'##vso[task.setvariable variable=BackBranch]{back}')
    print(f'##vso[task.setvariable variable=FeatureNumber]{feature_number}')
    print(f'##vso[task.setvariable variable=HelmBranch]{helm}')
except Exception as e:
    print(f"An error occurred: {e}")
